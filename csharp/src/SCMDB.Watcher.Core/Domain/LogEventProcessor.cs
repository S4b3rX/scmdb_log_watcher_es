using System.Globalization;
using System.Text.RegularExpressions;

namespace SCMDB.Watcher.Core.Domain;

public static partial class LogEventProcessor
{
    private const double BlueprintCorrelationWindowSeconds = 5.0d;

    public static double? ParseLogTimestamp(string line)
    {
        var match = TimestampPattern().Match(line);
        if (!match.Success)
        {
            return null;
        }

        var raw = match.Groups[1].Value.Replace("Z", "+00:00", StringComparison.Ordinal);
        if (!DateTimeOffset.TryParse(raw, CultureInfo.InvariantCulture, DateTimeStyles.RoundtripKind, out var timestamp))
        {
            return null;
        }

        return timestamp.ToUnixTimeMilliseconds() / 1000.0d;
    }

    public static void ProcessLine(string line, WatcherState state, IWatcherEventSink sink)
    {
        ArgumentNullException.ThrowIfNull(line);
        ArgumentNullException.ThrowIfNull(state);
        ArgumentNullException.ThrowIfNull(sink);

        var ts = ParseLogTimestamp(line) ?? DateTimeOffset.UtcNow.ToUnixTimeMilliseconds() / 1000.0d;

        var markerMatch = MarkerPattern().Match(line);
        if (markerMatch.Success)
        {
            state.RecordMarker(markerMatch.Groups[1].Value, markerMatch.Groups[2].Value, markerMatch.Groups[3].Value);
            return;
        }

        var acceptedMatch = AcceptedPattern().Match(line);
        if (acceptedMatch.Success)
        {
            var activeMission = state.RecordAccepted(acceptedMatch.Groups[1].Value, ts);
            if (activeMission is null)
            {
                return;
            }

            sink.Broadcast(new MissionStartEvent(activeMission.Guid, activeMission.DebugName, activeMission.Generator, activeMission.StartTs));
            return;
        }

        var endMissionMatch = EndMissionPattern().Match(line);
        if (endMissionMatch.Success)
        {
            var guid = endMissionMatch.Groups[1].Value;
            var completion = endMissionMatch.Groups[2].Value;
            var reason = endMissionMatch.Groups[3].Value;
            var activeMission = state.RecordEnd(guid, completion, ts);
            var entry = state.GetMissionEntry(guid);
            var debugName = activeMission?.DebugName ?? entry?.DebugName;
            var generator = activeMission?.Generator ?? entry?.Generator;

            if (completion == "Complete")
            {
                sink.Broadcast(new MissionCompleteEvent(guid, debugName, generator, completion, reason, ts));
            }
            else
            {
                sink.Broadcast(new MissionEndedEvent(guid, debugName, generator, completion, reason, ts));
            }

            return;
        }

        var blueprintMatch = BlueprintPattern().Match(line);
        if (blueprintMatch.Success)
        {
            var productName = blueprintMatch.Groups[1].Value.Trim();
            var correlation = state.CorrelateBlueprint(ts, BlueprintCorrelationWindowSeconds);
            sink.Broadcast(
                new BlueprintReceivedEvent(
                    productName,
                    correlation?.Guid,
                    correlation?.DebugName,
                    correlation?.Trigger,
                    ts));
        }
    }

    [GeneratedRegex("^<([0-9T:\\-.Z]+)>", RegexOptions.Compiled | RegexOptions.CultureInvariant)]
    private static partial Regex TimestampPattern();

    [GeneratedRegex("CreateMarker.*missionId \\[([^\\]]+)\\].*generator name \\[([^\\]]+)\\].*contract \\[([^\\]]+)\\]", RegexOptions.Compiled | RegexOptions.CultureInvariant)]
    private static partial Regex MarkerPattern();

    [GeneratedRegex("Added notification \"Contract Accepted:.*?MissionId: \\[([^\\]]+)\\]", RegexOptions.Compiled | RegexOptions.CultureInvariant)]
    private static partial Regex AcceptedPattern();

    [GeneratedRegex("<EndMission>.*MissionId\\[([^\\]]+)\\].*CompletionType\\[(\\w+)\\].*Reason\\[([^\\]]+)\\]", RegexOptions.Compiled | RegexOptions.CultureInvariant)]
    private static partial Regex EndMissionPattern();

    [GeneratedRegex("Added notification \"Received Blueprint: ([^:]+):", RegexOptions.Compiled | RegexOptions.CultureInvariant)]
    private static partial Regex BlueprintPattern();

    internal static Regex MarkerPatternForImport() => MarkerPattern();

    internal static Regex AcceptedPatternForImport() => AcceptedPattern();

    internal static Regex EndMissionPatternForImport() => EndMissionPattern();

    internal static Regex BlueprintPatternForImport() => BlueprintPattern();
}
