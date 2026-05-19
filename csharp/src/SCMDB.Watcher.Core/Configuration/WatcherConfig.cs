using System.Text.Json.Serialization;

namespace SCMDB.Watcher.Core.Configuration;

public sealed class WatcherConfig
{
    [JsonPropertyName("game_install_dir")]
    public string GameInstallDirectory { get; init; } = string.Empty;

    [JsonPropertyName("channel")]
    public string Channel { get; init; } = "LIVE";

    [JsonPropertyName("log_path")]
    public string LogPath { get; init; } = string.Empty;

    [JsonPropertyName("language")]
    public string Language { get; init; } = "es";

    public WatcherConfig Normalize()
    {
        var normalizedGameInstallDirectory = GameInstallDirectory.Trim();
        var normalizedChannel = WatcherPaths.NormalizeChannel(Channel);
        var normalizedLanguage = WatcherPaths.NormalizeLanguage(Language);
        var normalizedLogPath = string.IsNullOrWhiteSpace(LogPath) && !string.IsNullOrWhiteSpace(normalizedGameInstallDirectory)
            ? WatcherPaths.BuildLogPath(normalizedGameInstallDirectory, normalizedChannel)
            : LogPath.Trim();

        return new WatcherConfig
        {
            GameInstallDirectory = normalizedGameInstallDirectory,
            Channel = normalizedChannel,
            LogPath = normalizedLogPath,
            Language = normalizedLanguage,
        };
    }
}