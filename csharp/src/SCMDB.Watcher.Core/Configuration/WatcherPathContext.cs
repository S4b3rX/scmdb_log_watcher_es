namespace SCMDB.Watcher.Core.Configuration;

public sealed record WatcherPathContext(
    string BaseDirectory,
    string DataDirectory,
    string RuntimeDirectory,
    string ConfigPath);