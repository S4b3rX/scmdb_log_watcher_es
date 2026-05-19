using System.Net;
using System.Net.Http.Json;
using System.Net.Sockets;
using SCMDB.Watcher.Core.Domain;
using SCMDB.Watcher.Core.LocalApi;

namespace SCMDB.Watcher.Core.Tests.LocalApi;

public sealed class WatcherLocalApiServerTests
{
    [Fact]
    public async Task Ping_ReturnsStatusAndVersion()
    {
        using var fixture = new ServerFixture();
        using var client = new HttpClient();

        var payload = await client.GetFromJsonAsync<PingPayload>($"http://127.0.0.1:{fixture.Port}/ping");

        Assert.NotNull(payload);
        Assert.Equal("ok", payload!.Status);
        Assert.Equal("0.1.2", payload.Version);
    }

    [Fact]
    public async Task State_ReturnsActiveMissionSnapshot()
    {
        using var fixture = new ServerFixture();
        LogEventProcessor.ProcessLine(
            "<2026-05-17T12:00:00.000Z> CreateMarker missionId [guid-1] generator name [gen-a] contract [Contract A]",
            fixture.State,
            fixture.Bus);
        LogEventProcessor.ProcessLine(
            "<2026-05-17T12:00:02.000Z> Added notification \"Contract Accepted: foo MissionId: [guid-1]\"",
            fixture.State,
            fixture.Bus);

        using var client = new HttpClient();
        var payload = await client.GetFromJsonAsync<StatePayload>($"http://127.0.0.1:{fixture.Port}/state");

        Assert.NotNull(payload);
        var mission = Assert.Single(payload!.Active);
        Assert.Equal("guid-1", mission.Guid);
        Assert.Equal("Contract A", mission.DebugName);
    }

    [Fact]
    public async Task Events_SendsInitialSnapshot_AndBroadcastEvents()
    {
        using var fixture = new ServerFixture();
        using var client = new HttpClient();
        using var response = await client.GetAsync($"http://127.0.0.1:{fixture.Port}/events", HttpCompletionOption.ResponseHeadersRead);
        response.EnsureSuccessStatusCode();

        await using var stream = await response.Content.ReadAsStreamAsync();
        using var reader = new StreamReader(stream);

        var snapshotLine = await ReadNextDataLineAsync(reader);
        Assert.Contains("\"type\":\"state_snapshot\"", snapshotLine);

        LogEventProcessor.ProcessLine(
            "<2026-05-17T12:00:00.000Z> CreateMarker missionId [guid-2] generator name [gen-b] contract [Contract B]",
            fixture.State,
            fixture.Bus);
        LogEventProcessor.ProcessLine(
            "<2026-05-17T12:00:02.000Z> Added notification \"Contract Accepted: foo MissionId: [guid-2]\"",
            fixture.State,
            fixture.Bus);

        var missionStartLine = await ReadNextDataLineAsync(reader);
        Assert.Contains("\"type\":\"mission_start\"", missionStartLine);
        Assert.Contains("\"guid\":\"guid-2\"", missionStartLine);
    }

    private static async Task<string> ReadNextDataLineAsync(StreamReader reader)
    {
        var timeout = Task.Delay(TimeSpan.FromSeconds(5));
        while (true)
        {
            var readTask = reader.ReadLineAsync();
            var completed = await Task.WhenAny(readTask, timeout);
            if (completed == timeout)
            {
                throw new TimeoutException("Timed out waiting for SSE line.");
            }

            var line = await readTask;
            if (line is not null && line.StartsWith("data: ", StringComparison.Ordinal))
            {
                return line;
            }
        }
    }

    private sealed class ServerFixture : IDisposable
    {
        public ServerFixture()
        {
            Port = GetFreePort();
            State = new WatcherState();
            Bus = new EventBus();
            Server = new WatcherLocalApiServer(State, Bus, ["https://scmdb.net"], "0.1.2");
            Server.Start(Port);
        }

        public int Port { get; }

        public WatcherState State { get; }

        public EventBus Bus { get; }

        public WatcherLocalApiServer Server { get; }

        public void Dispose()
        {
            Server.Dispose();
        }

        private static int GetFreePort()
        {
            using var listener = new TcpListener(IPAddress.Loopback, 0);
            listener.Start();
            return ((IPEndPoint)listener.LocalEndpoint).Port;
        }
    }

    private sealed record PingPayload(string Status, string Version);

    private sealed record StatePayload(IReadOnlyList<ActiveMission> Active);
}
