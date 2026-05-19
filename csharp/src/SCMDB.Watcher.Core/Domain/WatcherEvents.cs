using System.Text.Json.Serialization;

namespace SCMDB.Watcher.Core.Domain;

public sealed record MissionEntry(string DebugName, string Generator);

public sealed record ActiveMission(
    [property: JsonPropertyName("guid")] string Guid,
    [property: JsonPropertyName("debugName")] string DebugName,
    [property: JsonPropertyName("generator")] string Generator,
    [property: JsonPropertyName("startTs")] double StartTs);

public sealed record MissionLifecycleEvent(string Trigger, string Guid, string DebugName, double Ts);

public abstract record WatcherEvent([property: JsonPropertyName("type")] string Type);

public sealed record StateSnapshotEvent(
    [property: JsonPropertyName("active")] IReadOnlyList<ActiveMission> Active)
    : WatcherEvent("state_snapshot");

public sealed record SessionResetEvent() : WatcherEvent("session_reset");

public sealed record MissionStartEvent(
    [property: JsonPropertyName("guid")] string Guid,
    [property: JsonPropertyName("debugName")] string DebugName,
    [property: JsonPropertyName("generator")] string Generator,
    [property: JsonPropertyName("startTs")] double StartTs)
    : WatcherEvent("mission_start");

public sealed record MissionCompleteEvent(
    [property: JsonPropertyName("guid")] string Guid,
    [property: JsonPropertyName("debugName")] string? DebugName,
    [property: JsonPropertyName("generator")] string? Generator,
    [property: JsonPropertyName("completion")] string Completion,
    [property: JsonPropertyName("reason")] string Reason,
    [property: JsonPropertyName("endTs")] double EndTs)
    : WatcherEvent("mission_complete");

public sealed record MissionEndedEvent(
    [property: JsonPropertyName("guid")] string Guid,
    [property: JsonPropertyName("debugName")] string? DebugName,
    [property: JsonPropertyName("generator")] string? Generator,
    [property: JsonPropertyName("completion")] string Completion,
    [property: JsonPropertyName("reason")] string Reason,
    [property: JsonPropertyName("endTs")] double EndTs)
    : WatcherEvent("mission_ended");

public sealed record BlueprintReceivedEvent(
    [property: JsonPropertyName("productName")] string ProductName,
    [property: JsonPropertyName("missionGuid")] string? MissionGuid,
    [property: JsonPropertyName("missionDebugName")] string? MissionDebugName,
    [property: JsonPropertyName("missionTrigger")] string? MissionTrigger,
    [property: JsonPropertyName("ts")] double Ts)
    : WatcherEvent("blueprint_received");

public interface IWatcherEventSink
{
    void Broadcast(WatcherEvent watcherEvent);
}
