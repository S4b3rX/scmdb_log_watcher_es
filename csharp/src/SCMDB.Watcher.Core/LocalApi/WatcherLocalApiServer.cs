using System.Net;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using SCMDB.Watcher.Core.Domain;

namespace SCMDB.Watcher.Core.LocalApi;

public sealed class WatcherLocalApiServer : IDisposable
{
    private const double HeartbeatSeconds = 15.0d;

    private static readonly JsonSerializerOptions SerializerOptions = new()
    {
        DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
    };

    private readonly WatcherState _state;
    private readonly EventBus _bus;
    private readonly HashSet<string> _allowedOrigins;
    private readonly string _version;
    private readonly HttpListener _listener = new();
    private readonly CancellationTokenSource _stopCts = new();
    private Task? _acceptLoopTask;

    public WatcherLocalApiServer(WatcherState state, EventBus bus, IEnumerable<string> allowedOrigins, string version)
    {
        _state = state;
        _bus = bus;
        _allowedOrigins = new HashSet<string>(allowedOrigins, StringComparer.OrdinalIgnoreCase);
        _version = version;
    }

    public int Port { get; private set; }

    public void Start(int port)
    {
        if (_listener.IsListening)
        {
            throw new InvalidOperationException("Watcher local API server is already running.");
        }

        Port = port;
        _listener.Prefixes.Clear();
        _listener.Prefixes.Add($"http://127.0.0.1:{port}/");
        _listener.Start();
        _acceptLoopTask = Task.Run(() => AcceptLoopAsync(_stopCts.Token));
    }

    public void Dispose()
    {
        _stopCts.Cancel();
        if (_listener.IsListening)
        {
            _listener.Stop();
        }

        _listener.Close();
        try
        {
            _acceptLoopTask?.GetAwaiter().GetResult();
        }
        catch (OperationCanceledException)
        {
        }
        catch (HttpListenerException)
        {
        }

        _stopCts.Dispose();
    }

    private async Task AcceptLoopAsync(CancellationToken cancellationToken)
    {
        while (!cancellationToken.IsCancellationRequested)
        {
            HttpListenerContext? context = null;
            try
            {
                context = await _listener.GetContextAsync();
            }
            catch (ObjectDisposedException) when (cancellationToken.IsCancellationRequested)
            {
                break;
            }
            catch (HttpListenerException) when (cancellationToken.IsCancellationRequested || !_listener.IsListening)
            {
                break;
            }

            _ = Task.Run(() => HandleContextAsync(context, cancellationToken), cancellationToken);
        }
    }

    private async Task HandleContextAsync(HttpListenerContext context, CancellationToken cancellationToken)
    {
        try
        {
            AddCorsHeaders(context.Request, context.Response);

            var path = context.Request.Url?.AbsolutePath ?? string.Empty;
            if (context.Request.HttpMethod != "GET")
            {
                context.Response.StatusCode = (int)HttpStatusCode.MethodNotAllowed;
                context.Response.Close();
                return;
            }

            switch (path)
            {
                case "/ping":
                    await WriteJsonAsync(context.Response, new { status = "ok", version = _version }, cancellationToken);
                    break;
                case "/state":
                    await WriteJsonAsync(context.Response, new { active = _state.SnapshotActive() }, cancellationToken);
                    break;
                case "/events":
                    await HandleEventsAsync(context.Response, cancellationToken);
                    break;
                default:
                    context.Response.StatusCode = (int)HttpStatusCode.NotFound;
                    context.Response.Close();
                    break;
            }
        }
        catch (HttpListenerException) when (cancellationToken.IsCancellationRequested)
        {
        }
        catch (ObjectDisposedException) when (cancellationToken.IsCancellationRequested)
        {
        }
    }

    private void AddCorsHeaders(HttpListenerRequest request, HttpListenerResponse response)
    {
        var origin = request.Headers["Origin"];
        if (!string.IsNullOrWhiteSpace(origin) && _allowedOrigins.Contains(origin))
        {
            response.Headers["Access-Control-Allow-Origin"] = origin;
            response.Headers[HttpResponseHeader.Vary] = "Origin";
        }
    }

    private static async Task WriteJsonAsync(HttpListenerResponse response, object payload, CancellationToken cancellationToken)
    {
        response.StatusCode = (int)HttpStatusCode.OK;
        response.ContentType = "application/json";
        await JsonSerializer.SerializeAsync(response.OutputStream, payload, SerializerOptions, cancellationToken);
        response.Close();
    }

    private async Task HandleEventsAsync(HttpListenerResponse response, CancellationToken cancellationToken)
    {
        var subscription = _bus.Subscribe();
        response.StatusCode = (int)HttpStatusCode.OK;
        response.ContentType = "text/event-stream";
        response.SendChunked = true;
        response.Headers[HttpResponseHeader.CacheControl] = "no-cache";
        response.Headers["X-Accel-Buffering"] = "no";
        response.Headers[HttpResponseHeader.Connection] = "keep-alive";

        try
        {
            using var writer = new StreamWriter(response.OutputStream, new UTF8Encoding(encoderShouldEmitUTF8Identifier: false), leaveOpen: false);
            await writer.WriteAsync($"data: {JsonSerializer.Serialize(new StateSnapshotEvent(_state.SnapshotActive()), SerializerOptions)}\n\n");
            await writer.FlushAsync(cancellationToken);

            while (!cancellationToken.IsCancellationRequested)
            {
                var readTask = subscription.Reader.ReadAsync(cancellationToken).AsTask();
                var completed = await Task.WhenAny(readTask, Task.Delay(TimeSpan.FromSeconds(HeartbeatSeconds), cancellationToken));
                if (completed == readTask)
                {
                    var payload = await readTask;
                    await writer.WriteAsync($"data: {payload}\n\n");
                }
                else
                {
                    await writer.WriteAsync(": heartbeat\n\n");
                }

                await writer.FlushAsync(cancellationToken);
            }
        }
        catch (OperationCanceledException)
        {
        }
        catch (HttpListenerException)
        {
        }
        catch (IOException)
        {
        }
        finally
        {
            _bus.Unsubscribe(subscription.Id);
            response.Close();
        }
    }
}
