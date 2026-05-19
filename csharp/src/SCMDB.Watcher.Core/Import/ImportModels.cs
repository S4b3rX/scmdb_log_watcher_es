using System.Text.Json.Serialization;

namespace SCMDB.Watcher.Core.Import;

public sealed record MissionImportRecord(
    [property: JsonPropertyName("guid")] string Guid,
    [property: JsonPropertyName("debugName")] string DebugName,
    [property: JsonPropertyName("generator")] string Generator,
    [property: JsonPropertyName("startTs")] double StartTs,
    [property: JsonPropertyName("endTs")] double EndTs,
    [property: JsonPropertyName("durationSec")] double DurationSec,
    [property: JsonPropertyName("reason")] string Reason);

public sealed record BlueprintImportRecord(
    [property: JsonPropertyName("productName")] string ProductName,
    [property: JsonPropertyName("ts")] double Ts,
    [property: JsonPropertyName("missionGuid")] string MissionGuid,
    [property: JsonPropertyName("missionDebugName")] string MissionDebugName,
    [property: JsonPropertyName("missionTrigger")] string MissionTrigger);

public sealed record ImportExportPayload(
    [property: JsonPropertyName("exportSchemaVersion")] int ExportSchemaVersion,
    [property: JsonPropertyName("watcherVersion")] string WatcherVersion,
    [property: JsonPropertyName("exportedAt")] string ExportedAt,
    [property: JsonPropertyName("sourceLogs")] IReadOnlyList<string> SourceLogs,
    [property: JsonPropertyName("missions")] IReadOnlyList<MissionImportRecord> Missions,
    [property: JsonPropertyName("blueprints")] IReadOnlyList<BlueprintImportRecord> Blueprints);
