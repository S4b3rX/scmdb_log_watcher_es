using System.IO;
using System.Text.Json;
using SCMDB.Watcher.Core.Configuration;

namespace SCMDB.Watcher.Core.Tests.Configuration;

public sealed class WatcherConfigStoreTests
{
    [Fact]
    public void Resolve_UsesLocalAppData_WhenRequested()
    {
        using var temp = new TempDirectory();

        var paths = WatcherPaths.Resolve(temp.Path, preferLocalAppData: true, localAppDataOverride: temp.Path);

        Assert.Equal(Path.Combine(temp.Path, WatcherPaths.AppDataDirectoryName), paths.DataDirectory);
        Assert.Equal(Path.Combine(paths.DataDirectory, WatcherPaths.RuntimeDirectoryName), paths.RuntimeDirectory);
        Assert.Equal(Path.Combine(paths.RuntimeDirectory, WatcherPaths.ConfigFileName), paths.ConfigPath);
        Assert.True(Directory.Exists(paths.RuntimeDirectory));
    }

    [Fact]
    public void Resolve_FallsBackToBaseDirectory_WhenLocalAppDataIsMissing()
    {
        using var temp = new TempDirectory();

        var paths = WatcherPaths.Resolve(temp.Path, preferLocalAppData: true, localAppDataOverride: "   ");

        Assert.Equal(Path.GetFullPath(temp.Path), paths.DataDirectory);
        Assert.Equal(Path.Combine(paths.DataDirectory, WatcherPaths.RuntimeDirectoryName), paths.RuntimeDirectory);
    }

    [Fact]
    public void Load_ReturnsDefaultConfig_WhenFileIsMissing()
    {
        using var temp = new TempDirectory();
        var store = new WatcherConfigStore(WatcherPaths.Resolve(temp.Path, preferLocalAppData: false));

        var config = store.Load();

        Assert.Equal(string.Empty, config.GameInstallDirectory);
        Assert.Equal("LIVE", config.Channel);
        Assert.Equal(string.Empty, config.LogPath);
        Assert.Equal("es", config.Language);
    }

    [Fact]
    public void Save_NormalizesConfig_AndBuildsMissingLogPath()
    {
        using var temp = new TempDirectory();
        var store = new WatcherConfigStore(WatcherPaths.Resolve(temp.Path, preferLocalAppData: false));

        store.Save(new WatcherConfig
        {
            GameInstallDirectory = " C:/Games/StarCitizen ",
            Channel = "hotfix",
            Language = "EN",
            LogPath = string.Empty,
        });

        var config = store.Load();

        Assert.Equal("C:/Games/StarCitizen", config.GameInstallDirectory);
        Assert.Equal("HOTFIX", config.Channel);
        Assert.Equal("en", config.Language);
        Assert.EndsWith(Path.Combine("HOTFIX", "Game.log"), config.LogPath);
    }

    [Fact]
    public void Load_IgnoresInvalidJson_AndReturnsDefaults()
    {
        using var temp = new TempDirectory();
        var paths = WatcherPaths.Resolve(temp.Path, preferLocalAppData: false);
        File.WriteAllText(paths.ConfigPath, "{ invalid json }");

        var store = new WatcherConfigStore(paths);
        var config = store.Load();

        Assert.Equal(string.Empty, config.GameInstallDirectory);
        Assert.Equal("LIVE", config.Channel);
    }

    [Fact]
    public void Save_WritesExpectedJsonShape()
    {
        using var temp = new TempDirectory();
        var paths = WatcherPaths.Resolve(temp.Path, preferLocalAppData: false);
        var store = new WatcherConfigStore(paths);

        store.Save(new WatcherConfig
        {
            GameInstallDirectory = "D:/RSI/StarCitizen",
            Channel = "LIVE",
            LogPath = "D:/RSI/StarCitizen/LIVE/Game.log",
            Language = "es",
        });

        using var document = JsonDocument.Parse(File.ReadAllText(paths.ConfigPath));
        var root = document.RootElement;

        Assert.Equal("D:/RSI/StarCitizen", root.GetProperty("game_install_dir").GetString());
        Assert.Equal("LIVE", root.GetProperty("channel").GetString());
        Assert.Equal("D:/RSI/StarCitizen/LIVE/Game.log", root.GetProperty("log_path").GetString());
        Assert.Equal("es", root.GetProperty("language").GetString());
    }

    private sealed class TempDirectory : IDisposable
    {
        public TempDirectory()
        {
            Path = System.IO.Path.Combine(System.IO.Path.GetTempPath(), $"scmdb-csharp-tests-{Guid.NewGuid():N}");
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