using SCMDB.Watcher.Core.Import;

namespace SCMDB.Watcher.Core.Tests.Import;

public sealed class ImportExportServiceTests
{
    [Fact]
    public void CollectLogFiles_OptionallyIncludesCurrentLog()
    {
        using var temp = new TempDirectory();
        var backups = Path.Combine(temp.Path, "logbackups");
        Directory.CreateDirectory(backups);
        File.WriteAllText(Path.Combine(backups, "Game Build(1).log"), string.Empty);
        File.WriteAllText(Path.Combine(backups, "Game Build(2).log"), string.Empty);
        var current = Path.Combine(temp.Path, "Game.log");
        File.WriteAllText(current, string.Empty);

        var files = ImportExportService.CollectLogFiles(backups, current, includeCurrent: true);

        Assert.Equal(3, files.Count);
        Assert.Equal(current, files.Last());
    }

    [Fact]
    public void DedupeMissionsByGuid_RemovesDuplicates()
    {
        var missions = new[]
        {
            new MissionImportRecord("a", "A", "gen", 1, 2, 1, "ok"),
            new MissionImportRecord("b", "B", "gen", 1, 2, 1, "ok"),
            new MissionImportRecord("a", "A2", "gen", 1, 2, 1, "ok"),
        };

        var (deduped, dropped) = ImportExportService.DedupeMissionsByGuid(missions);

        Assert.Equal(2, deduped.Count);
        Assert.Equal(1, dropped);
    }

    [Fact]
    public void ResolveOutputPath_DefaultsToRuntimeImportsFolder()
    {
        using var temp = new TempDirectory();

        var outputPath = ImportExportService.ResolveOutputPath(null, temp.Path, preferLocalAppData: false);

        Assert.Equal("imports", Path.GetFileName(Path.GetDirectoryName(outputPath)!));
        Assert.StartsWith("scmdb-import-", Path.GetFileName(outputPath));
    }

    [Fact]
    public void ScanFileForExport_ProcessesMinimalMissionAndBlueprintFlow()
    {
        using var temp = new TempDirectory();
        var path = Path.Combine(temp.Path, "sample.log");
        File.WriteAllText(
            path,
            string.Join(Environment.NewLine, new[]
            {
                "<2026-05-17T12:00:00.000Z> CreateMarker missionId [guid-1] generator name [gen] contract [Contract A]",
                "<2026-05-17T12:00:01.000Z> Added notification \"Contract Accepted: test MissionId: [guid-1]\"",
                "<2026-05-17T12:00:05.000Z> <EndMission> MissionId[guid-1] CompletionType[Complete] Reason[Complete]",
                "<2026-05-17T12:00:06.000Z> Added notification \"Received Blueprint: Product X:\"",
            }));

        var (missions, blueprints) = ImportExportService.ScanFileForExport(path);

        var mission = Assert.Single(missions);
        Assert.Equal("guid-1", mission.Guid);
        var blueprint = Assert.Single(blueprints);
        Assert.Equal("guid-1", blueprint.MissionGuid);
    }

    [Fact]
    public void BuildExportPayload_UsesExpectedWatcherVersion()
    {
        var payload = ImportExportService.BuildExportPayload(
            "0.1.2",
            ["a.log"],
            [new MissionImportRecord("x", "A", "gen", 1, 2, 1, "ok")],
            [new BlueprintImportRecord("p", 2, "x", "A", "complete")]);

        Assert.Equal("0.1.2", payload.WatcherVersion);
        Assert.Equal(["a.log"], payload.SourceLogs);
    }

    private sealed class TempDirectory : IDisposable
    {
        public TempDirectory()
        {
            Path = System.IO.Path.Combine(System.IO.Path.GetTempPath(), $"scmdb-import-tests-{Guid.NewGuid():N}");
            Directory.CreateDirectory(Path);
        }

        public string Path { get; }

        public void Dispose()
        {
            try
            {
                Directory.Delete(Path, recursive: true);
            }
            catch (IOException)
            {
            }
            catch (UnauthorizedAccessException)
            {
            }
        }
    }
}
