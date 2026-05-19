using System.Diagnostics;
using SCMDB.Watcher.Core.Configuration;
using SCMDB.Watcher.Core.Import;
using SCMDB.Watcher.Core.Runtime;

namespace SCMDB.Watcher.Desktop;

public partial class Form1 : Form
{
    private const int DefaultPort = 23456;
    private const string WatcherVersion = "0.1.2";
    private static readonly string[] ProdOrigins = ["https://scmdb.net", "https://www.scmdb.net"];

    private readonly WatcherPathContext _paths;
    private readonly WatcherConfigStore _configStore;
    private readonly System.Windows.Forms.Timer _statusTimer;
    private WatcherConfig _config = new();
    private WatcherRuntimeHost? _runtimeHost;

    public Form1()
    {
        InitializeComponent();

        _paths = WatcherPaths.Resolve(AppContext.BaseDirectory, preferLocalAppData: true);
        _configStore = new WatcherConfigStore(_paths);
        _statusTimer = new System.Windows.Forms.Timer { Interval = 1000 };
        Load += OnLoad;
        FormClosed += OnFormClosed;
        btnStart.Click += (_, _) => StartRuntime();
        btnStop.Click += (_, _) => StopRuntime();
        btnReload.Click += (_, _) => ReloadConfiguration();
        btnSaveConfig.Click += (_, _) => SaveConfiguration();
        btnBrowseGameDir.Click += (_, _) => BrowseGameDirectory();
        btnBrowseLogPath.Click += (_, _) => BrowseLogPath();
        btnImport.Click += async (_, _) => await RunImportAsync();
        btnOpenRuntime.Click += (_, _) => OpenRuntimeDirectory();
        cmbChannel.SelectedIndexChanged += (_, _) => AutoFillLogPathFromConfigInputs();
        _statusTimer.Tick += (_, _) => RefreshUi();
    }

    private void OnLoad(object? sender, EventArgs e)
    {
        _config = _configStore.Load();
        ApplyConfigToInputs();
        TryAutoStartRuntime();
        _statusTimer.Start();
        RefreshUi();
    }

    private void OnFormClosed(object? sender, FormClosedEventArgs e)
    {
        _statusTimer.Stop();
        StopRuntime();
    }

    private void ReloadConfiguration()
    {
        var wasRunning = _runtimeHost is not null;
        StopRuntime();
        _config = _configStore.Load();
        ApplyConfigToInputs();
        if (wasRunning)
        {
            StartRuntime();
        }

        RefreshUi();
    }

    private void TryAutoStartRuntime()
    {
        if (string.IsNullOrWhiteSpace(_config.LogPath))
        {
            return;
        }

        try
        {
            StartRuntime();
        }
        catch
        {
            RefreshUi("Runtime failed to start automatically.");
        }
    }

    private void ApplyConfigToInputs()
    {
        txtGameDir.Text = _config.GameInstallDirectory;
        txtLogPath.Text = _config.LogPath;
        cmbChannel.SelectedItem = WatcherPaths.NormalizeChannel(_config.Channel);
        cmbLanguage.SelectedItem = WatcherPaths.NormalizeLanguage(_config.Language);
        if (cmbChannel.SelectedIndex < 0)
        {
            cmbChannel.SelectedIndex = 0;
        }

        if (cmbLanguage.SelectedIndex < 0)
        {
            cmbLanguage.SelectedIndex = 0;
        }
    }

    private WatcherConfig ReadConfigFromInputs()
    {
        return new WatcherConfig
        {
            GameInstallDirectory = txtGameDir.Text,
            Channel = cmbChannel.SelectedItem?.ToString() ?? "LIVE",
            LogPath = txtLogPath.Text,
            Language = cmbLanguage.SelectedItem?.ToString() ?? "es",
        }.Normalize();
    }

    private void SaveConfiguration()
    {
        var wasRunning = _runtimeHost is not null;
        if (wasRunning)
        {
            StopRuntime();
        }

        _config = ReadConfigFromInputs();
        _configStore.Save(_config);
        ApplyConfigToInputs();

        if (wasRunning)
        {
            StartRuntime();
        }

        RefreshUi("Configuration saved.");
    }

    private void BrowseGameDirectory()
    {
        using var dialog = new FolderBrowserDialog
        {
            ShowNewFolderButton = false,
            InitialDirectory = Directory.Exists(txtGameDir.Text) ? txtGameDir.Text : Environment.GetFolderPath(Environment.SpecialFolder.MyComputer),
        };

        if (dialog.ShowDialog(this) != DialogResult.OK || string.IsNullOrWhiteSpace(dialog.SelectedPath))
        {
            return;
        }

        txtGameDir.Text = dialog.SelectedPath;
        AutoFillLogPathFromConfigInputs();
    }

    private void BrowseLogPath()
    {
        using var dialog = new OpenFileDialog
        {
            CheckFileExists = false,
            FileName = Path.GetFileName(string.IsNullOrWhiteSpace(txtLogPath.Text) ? "Game.log" : txtLogPath.Text),
            InitialDirectory = Directory.Exists(Path.GetDirectoryName(txtLogPath.Text)) ? Path.GetDirectoryName(txtLogPath.Text) : _paths.BaseDirectory,
            Filter = "Log files (*.log)|*.log|All files (*.*)|*.*",
        };

        if (dialog.ShowDialog(this) != DialogResult.OK || string.IsNullOrWhiteSpace(dialog.FileName))
        {
            return;
        }

        txtLogPath.Text = dialog.FileName;
    }

    private void AutoFillLogPathFromConfigInputs()
    {
        if (string.IsNullOrWhiteSpace(txtGameDir.Text))
        {
            return;
        }

        if (!string.IsNullOrWhiteSpace(txtLogPath.Text) && !txtLogPath.Text.Contains("Game.log", StringComparison.OrdinalIgnoreCase))
        {
            return;
        }

        txtLogPath.Text = WatcherPaths.BuildLogPath(txtGameDir.Text, cmbChannel.SelectedItem?.ToString() ?? "LIVE");
    }

    private async Task RunImportAsync()
    {
        SaveConfiguration();
        btnImport.Enabled = false;

        try
        {
            var config = _config;
            if (string.IsNullOrWhiteSpace(config.LogPath))
            {
                RefreshUi("Import skipped: missing log_path.");
                return;
            }

            var currentLog = config.LogPath;
            var logBackupsDirectory = Path.Combine(Path.GetDirectoryName(currentLog) ?? string.Empty, "logbackups");
            var files = ImportExportService.CollectLogFiles(logBackupsDirectory, currentLog, includeCurrent: true);
            if (files.Count == 0)
            {
                RefreshUi("Import skipped: no log files found.");
                return;
            }

            var outputPath = await Task.Run(() =>
            {
                var missions = new List<MissionImportRecord>();
                var blueprints = new List<BlueprintImportRecord>();
                foreach (var file in files)
                {
                    var result = ImportExportService.ScanFileForExport(file);
                    missions.AddRange(result.Missions);
                    blueprints.AddRange(result.Blueprints);
                }

                var (dedupedMissions, _) = ImportExportService.DedupeMissionsByGuid(missions);
                var sourceLogs = files
                    .Select(path => Path.GetFileName(path) ?? path)
                    .ToList();
                var payload = ImportExportService.BuildExportPayload(WatcherVersion, sourceLogs, dedupedMissions, blueprints);
                var destination = ImportExportService.ResolveOutputPath(null, _paths.BaseDirectory, preferLocalAppData: true);
                ImportExportService.WritePayload(destination, payload);
                return destination;
            });

            RefreshUi($"Import completed: {outputPath}");
            var openFolder = MessageBox.Show(
                this,
                $"{outputPath}{Environment.NewLine}{Environment.NewLine}Open the export folder?",
                "Import completed",
                MessageBoxButtons.YesNo,
                MessageBoxIcon.Information);
            if (openFolder == DialogResult.Yes)
            {
                OpenPathInExplorer(outputPath);
            }
        }
        catch (Exception ex)
        {
            RefreshUi($"Import failed: {ex.Message}");
            MessageBox.Show(this, ex.Message, "Import failed", MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
        finally
        {
            btnImport.Enabled = true;
        }
    }

    private void OpenRuntimeDirectory()
    {
        OpenPathInExplorer(_paths.RuntimeDirectory);
    }

    private static void OpenPathInExplorer(string path)
    {
        var targetPath = string.IsNullOrWhiteSpace(path) ? string.Empty : path;
        if (string.IsNullOrWhiteSpace(targetPath))
        {
            return;
        }

        var fullPath = Path.GetFullPath(targetPath);
        var explorerArguments = File.Exists(fullPath)
            ? $"/select,\"{fullPath}\""
            : $"\"{(Directory.Exists(fullPath) ? fullPath : Path.GetDirectoryName(fullPath) ?? fullPath)}\"";

        Process.Start(new ProcessStartInfo
        {
            FileName = "explorer.exe",
            Arguments = explorerArguments,
            UseShellExecute = true,
        });
    }

    private void StartRuntime()
    {
        if (_runtimeHost is not null)
        {
            RefreshUi();
            return;
        }

        if (string.IsNullOrWhiteSpace(_config.LogPath))
        {
            RefreshUi("Missing log_path in watcher-config.json.");
            return;
        }

        try
        {
            _runtimeHost = new WatcherRuntimeHost(_config.LogPath, DefaultPort, ProdOrigins, WatcherVersion);
            _runtimeHost.Start();
            RefreshUi();
        }
        catch (Exception ex)
        {
            _runtimeHost?.Dispose();
            _runtimeHost = null;
            RefreshUi($"Runtime failed: {ex.Message}");
        }
    }

    private void StopRuntime()
    {
        _runtimeHost?.Dispose();
        _runtimeHost = null;
        RefreshUi();
    }

    private void RefreshUi(string? overrideStatus = null)
    {
        var statusText = overrideStatus
            ?? (_runtimeHost is null ? "Stopped" : $"Running on http://127.0.0.1:{_runtimeHost.Port}");

        lblStatus.Text = $"Status: {statusText}";
        lblStatus.ForeColor = _runtimeHost is null ? Color.Firebrick : Color.ForestGreen;
        btnStart.Enabled = _runtimeHost is null;
        btnStop.Enabled = _runtimeHost is not null;

        txtSummary.Text = string.Join(Environment.NewLine, new[]
        {
            "Estado del port actual a C#:",
            "- config/runtime paths portados",
            "- parser de Game.log portado",
            "- API localhost /ping /state /events portada",
            "- tailer live y runtime host portados",
            string.Empty,
            $"Base directory: {_paths.BaseDirectory}",
            $"Data directory: {_paths.DataDirectory}",
            $"Runtime directory: {_paths.RuntimeDirectory}",
            $"Config path: {_paths.ConfigPath}",
            string.Empty,
            $"game_install_dir: {_config.GameInstallDirectory}",
            $"channel: {_config.Channel}",
            $"log_path: {_config.LogPath}",
            $"language: {_config.Language}",
            string.Empty,
            $"watcher version: {WatcherVersion}",
            $"localhost port: {DefaultPort}",
            $"active missions: {_runtimeHost?.State.SnapshotActive().Count ?? 0}",
            $"runtime running: {_runtimeHost is not null}",
        });
    }
}
