using SCMDB.Watcher.Core.Domain;

namespace SCMDB.Watcher.Core.Tests.Domain;

public sealed class LogEventProcessorTests
{
    [Fact]
    public void MarkerThenAccept_EmitsMissionStart()
    {
        var state = new WatcherState();
        var sink = new FakeSink();

        LogEventProcessor.ProcessLine(
            "<2026-05-17T12:00:00.000Z> CreateMarker missionId [guid-1] generator name [gen-a] contract [Contract A]",
            state,
            sink);
        LogEventProcessor.ProcessLine(
            "<2026-05-17T12:00:02.000Z> Added notification \"Contract Accepted: foo MissionId: [guid-1]\"",
            state,
            sink);

        var missionStart = Assert.IsType<MissionStartEvent>(Assert.Single(sink.Events));
        Assert.Equal("guid-1", missionStart.Guid);
        Assert.Equal("Contract A", missionStart.DebugName);
        Assert.Equal("gen-a", missionStart.Generator);
    }

    [Fact]
    public void Complete_EmitsMissionComplete()
    {
        var state = new WatcherState();
        var sink = new FakeSink();

        LogEventProcessor.ProcessLine(
            "<2026-05-17T12:00:00.000Z> CreateMarker missionId [guid-2] generator name [gen-b] contract [Contract B]",
            state,
            sink);
        LogEventProcessor.ProcessLine(
            "<2026-05-17T12:00:01.000Z> Added notification \"Contract Accepted: bar MissionId: [guid-2]\"",
            state,
            sink);
        LogEventProcessor.ProcessLine(
            "<2026-05-17T12:00:05.000Z> <EndMission> MissionId[guid-2] CompletionType[Complete] Reason[Complete]",
            state,
            sink);

        var missionComplete = Assert.IsType<MissionCompleteEvent>(sink.Events.Last());
        Assert.Equal("guid-2", missionComplete.Guid);
        Assert.Equal("Contract B", missionComplete.DebugName);
    }

    [Fact]
    public void NonComplete_EmitsMissionEnded()
    {
        var state = new WatcherState();
        var sink = new FakeSink();

        LogEventProcessor.ProcessLine(
            "<2026-05-17T12:00:00.000Z> CreateMarker missionId [guid-4] generator name [gen-d] contract [Contract D]",
            state,
            sink);
        LogEventProcessor.ProcessLine(
            "<2026-05-17T12:00:01.000Z> Added notification \"Contract Accepted: bar MissionId: [guid-4]\"",
            state,
            sink);
        LogEventProcessor.ProcessLine(
            "<2026-05-17T12:00:05.000Z> <EndMission> MissionId[guid-4] CompletionType[Fail] Reason[Timeout]",
            state,
            sink);

        var missionEnded = Assert.IsType<MissionEndedEvent>(sink.Events.Last());
        Assert.Equal("Fail", missionEnded.Completion);
        Assert.Equal("Timeout", missionEnded.Reason);
    }

    [Fact]
    public void Blueprint_CorrelatesToRecentLifecycleEvent()
    {
        var state = new WatcherState();
        var sink = new FakeSink();

        LogEventProcessor.ProcessLine(
            "<2026-05-17T12:00:00.000Z> CreateMarker missionId [guid-3] generator name [gen-c] contract [Contract C]",
            state,
            sink);
        LogEventProcessor.ProcessLine(
            "<2026-05-17T12:00:01.000Z> Added notification \"Contract Accepted: baz MissionId: [guid-3]\"",
            state,
            sink);
        LogEventProcessor.ProcessLine(
            "<2026-05-17T12:00:02.000Z> Added notification \"Received Blueprint: Product X:\"",
            state,
            sink);

        var blueprint = Assert.IsType<BlueprintReceivedEvent>(sink.Events.Last());
        Assert.Equal("guid-3", blueprint.MissionGuid);
        Assert.Equal("Contract C", blueprint.MissionDebugName);
        Assert.Equal("accept", blueprint.MissionTrigger);
    }

    [Fact]
    public void ParseLogTimestamp_ReturnsUnixSeconds()
    {
        var timestamp = LogEventProcessor.ParseLogTimestamp("<2026-05-17T12:00:02.000Z> anything");

        Assert.NotNull(timestamp);
        Assert.Equal(1779019202d, timestamp!.Value);
    }

    private sealed class FakeSink : IWatcherEventSink
    {
        public List<WatcherEvent> Events { get; } = [];

        public void Broadcast(WatcherEvent watcherEvent)
        {
            Events.Add(watcherEvent);
        }
    }
}
