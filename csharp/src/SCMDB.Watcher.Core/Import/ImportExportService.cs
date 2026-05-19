using System.Text.Json;
using SCMDB.Watcher.Core.Configuration;
using SCMDB.Watcher.Core.Domain;

namespace SCMDB.Watcher.Core.Import;

public static class ImportExportService
{
    private sealed class NullSink : IWatcherEventSink
    {
        public void Broadcast(WatcherEvent watcherEvent)
        {
        }
    }

    public static (IReadOnlyList<MissionImportRecord> Missions, IReadOnlyList<BlueprintImportRecord> Blueprints) ScanFileForExport(string path)
    {
        var state = new WatcherState();
        var missions = new List<MissionImportRecord>();
        var blueprints = new List<BlueprintImportRecord>();
        var sink = new NullSink();

        if (!File.Exists(path))
        {
            return (missions, blueprints);
        }

        foreach (var line in File.ReadLines(path))
        {
            if (string.IsNullOrWhiteSpace(line))
            {
                continue;
            }

            var ts = LogEventProcessor.ParseLogTimestamp(line) ?? 0.0d;
            var markerMatch = LogEventProcessor.MarkerPatternForImport().Match(line);
            if (markerMatch.Success)
            {
                state.RecordMarker(markerMatch.Groups[1].Value, markerMatch.Groups[2].Value, markerMatch.Groups[3].Value);
                continue;
            }

            var acceptedMatch = LogEventProcessor.AcceptedPatternForImport().Match(line);
            if (acceptedMatch.Success)
            {
                state.RecordAccepted(acceptedMatch.Groups[1].Value, ts);
                continue;
            }

            var endMissionMatch = LogEventProcessor.EndMissionPatternForImport().Match(line);
            if (endMissionMatch.Success)
            {
                var guid = endMissionMatch.Groups[1].Value;
                var completion = endMissionMatch.Groups[2].Value;
                var reason = endMissionMatch.Groups[3].Value;
                var activeMission = state.RecordEnd(guid, completion, ts);
                if (completion == "Complete" && activeMission is not null)
                {
                    missions.Add(new MissionImportRecord(
                        guid,
                        activeMission.DebugName,
                        activeMission.Generator,
                        activeMission.StartTs,
                        ts,
                        Math.Round(ts - activeMission.StartTs, 3),
                        reason));
                }

                continue;
            }

            var blueprintMatch = LogEventProcessor.BlueprintPatternForImport().Match(line);
            if (blueprintMatch.Success)
            {
                var correlation = state.CorrelateBlueprint(ts);
                if (correlation is not null)
                {
                    blueprints.Add(new BlueprintImportRecord(
                        blueprintMatch.Groups[1].Value.Trim(),
                        ts,
                        correlation.Guid,
                        correlation.DebugName,
                        correlation.Trigger));
                }

                continue;
            }

            LogEventProcessor.ProcessLine(line, state, sink);
        }

        return (missions, blueprints);
    }

    public static IReadOnlyList<string> CollectLogFiles(string logBackupsDirectory, string currentLogPath, bool includeCurrent)
    {
        var files = Directory.Exists(logBackupsDirectory)
            ? Directory.GetFiles(logBackupsDirectory, "Game Build(*).log").OrderBy(path => path, StringComparer.OrdinalIgnoreCase).ToList()
            : [];

        if (includeCurrent && File.Exists(currentLogPath))
        {
            files.Add(currentLogPath);
        }

        return files;
    }

    public static (IReadOnlyList<MissionImportRecord> Missions, int Dropped) DedupeMissionsByGuid(IEnumerable<MissionImportRecord> missions)
    {
        var seen = new HashSet<string>(StringComparer.Ordinal);
        var deduped = new List<MissionImportRecord>();
        var dropped = 0;

        foreach (var mission in missions)
        {
            if (seen.Contains(mission.Guid))
            {
                dropped++;
                continue;
            }

            seen.Add(mission.Guid);
            deduped.Add(mission);
        }

        return (deduped, dropped);
    }

    public static string ResolveOutputPath(string? outputPath, string baseDirectory, bool preferLocalAppData)
    {
        if (!string.IsNullOrWhiteSpace(outputPath))
        {
            var fullOutputPath = Path.GetFullPath(outputPath);
            Directory.CreateDirectory(Path.GetDirectoryName(fullOutputPath)!);
            return fullOutputPath;
        }

        var paths = WatcherPaths.Resolve(baseDirectory, preferLocalAppData);
        var importsDirectory = Path.Combine(paths.RuntimeDirectory, "imports");
        Directory.CreateDirectory(importsDirectory);
        return Path.Combine(importsDirectory, $"scmdb-import-{DateTime.Now:yyyy-MM-dd_HH-mm-ss}.json");
    }

    public static ImportExportPayload BuildExportPayload(
        string watcherVersion,
        IReadOnlyList<string> sourceLogs,
        IReadOnlyList<MissionImportRecord> missions,
        IReadOnlyList<BlueprintImportRecord> blueprints)
    {
        return new ImportExportPayload(
            1,
            watcherVersion,
            DateTimeOffset.UtcNow.ToString("O"),
            sourceLogs,
            missions,
            blueprints);
    }

    public static void WritePayload(string outputPath, ImportExportPayload payload)
    {
        var json = JsonSerializer.Serialize(payload, new JsonSerializerOptions { WriteIndented = true });
        File.WriteAllText(outputPath, json);
    }
}
