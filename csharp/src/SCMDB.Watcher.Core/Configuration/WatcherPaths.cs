using System.IO;

namespace SCMDB.Watcher.Core.Configuration;

public static class WatcherPaths
{
    public const string ConfigFileName = "watcher-config.json";
    public const string RuntimeDirectoryName = "runtime";
    public const string AppDataDirectoryName = "SCMDB Log Watcher";

    public static WatcherPathContext Resolve(
        string baseDirectory,
        bool preferLocalAppData,
        string? localAppDataOverride = null)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(baseDirectory);

        var normalizedBaseDirectory = Path.GetFullPath(baseDirectory);
        var dataDirectory = normalizedBaseDirectory;

        if (preferLocalAppData)
        {
            var localAppData = localAppDataOverride is null
                ? Environment.GetEnvironmentVariable("LOCALAPPDATA")
                : localAppDataOverride;

            if (!string.IsNullOrWhiteSpace(localAppData))
            {
                dataDirectory = Path.Combine(localAppData.Trim(), AppDataDirectoryName);
                Directory.CreateDirectory(dataDirectory);
            }
        }

        var runtimeDirectory = Path.Combine(dataDirectory, RuntimeDirectoryName);
        Directory.CreateDirectory(runtimeDirectory);

        return new WatcherPathContext(
            BaseDirectory: normalizedBaseDirectory,
            DataDirectory: dataDirectory,
            RuntimeDirectory: runtimeDirectory,
            ConfigPath: Path.Combine(runtimeDirectory, ConfigFileName));
    }

    public static string NormalizeChannel(string? value, string fallback = "LIVE")
    {
        var candidate = (value ?? string.Empty).Trim().ToUpperInvariant();
        return candidate is "LIVE" or "HOTFIX" ? candidate : fallback;
    }

    public static string NormalizeLanguage(string? value, string fallback = "es")
    {
        var candidate = (value ?? string.Empty).Trim().ToLowerInvariant();
        return candidate is "es" or "en" ? candidate : fallback;
    }

    public static string BuildLogPath(string gameInstallDirectory, string channel)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(gameInstallDirectory);

        var normalizedGameDirectory = gameInstallDirectory.Trim();
        var normalizedChannel = NormalizeChannel(channel);
        var baseDirectory = new DirectoryInfo(normalizedGameDirectory);

        if (NormalizeChannel(baseDirectory.Name, string.Empty) is "LIVE" or "HOTFIX")
        {
            return Path.Combine(baseDirectory.FullName, "Game.log");
        }

        return Path.Combine(baseDirectory.FullName, normalizedChannel, "Game.log");
    }
}
