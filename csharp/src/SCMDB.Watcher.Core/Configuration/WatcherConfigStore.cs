using System.IO;
using System.Text.Json;

namespace SCMDB.Watcher.Core.Configuration;

public sealed class WatcherConfigStore
{
    private static readonly JsonSerializerOptions SerializerOptions = new()
    {
        WriteIndented = true,
        PropertyNameCaseInsensitive = true,
    };

    private readonly WatcherPathContext _pathContext;

    public WatcherConfigStore(WatcherPathContext pathContext)
    {
        _pathContext = pathContext;
    }

    public string ConfigPath => _pathContext.ConfigPath;

    public WatcherConfig Load()
    {
        if (!File.Exists(_pathContext.ConfigPath))
        {
            return new WatcherConfig();
        }

        try
        {
            var json = File.ReadAllText(_pathContext.ConfigPath);
            var config = JsonSerializer.Deserialize<WatcherConfig>(json, SerializerOptions);
            return (config ?? new WatcherConfig()).Normalize();
        }
        catch (IOException)
        {
            return new WatcherConfig();
        }
        catch (JsonException)
        {
            return new WatcherConfig();
        }
    }

    public void Save(WatcherConfig config)
    {
        ArgumentNullException.ThrowIfNull(config);

        var normalizedConfig = config.Normalize();
        Directory.CreateDirectory(Path.GetDirectoryName(_pathContext.ConfigPath)!);
        var json = JsonSerializer.Serialize(normalizedConfig, SerializerOptions);
        File.WriteAllText(_pathContext.ConfigPath, json);
    }
}