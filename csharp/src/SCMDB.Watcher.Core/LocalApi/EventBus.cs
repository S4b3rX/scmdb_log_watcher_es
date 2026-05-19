using System.Collections.Concurrent;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Threading.Channels;
using SCMDB.Watcher.Core.Domain;

namespace SCMDB.Watcher.Core.LocalApi;

public sealed class EventBus : IWatcherEventSink
{
    private const int SubscriberQueueMaxSize = 200;
    private static readonly JsonSerializerOptions SerializerOptions = new()
    {
        DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
    };

    private readonly ConcurrentDictionary<Guid, Channel<string>> _subscribers = new();

    public EventSubscription Subscribe()
    {
        var subscriptionId = Guid.NewGuid();
        var channel = Channel.CreateBounded<string>(new BoundedChannelOptions(SubscriberQueueMaxSize)
        {
            SingleReader = true,
            SingleWriter = false,
            FullMode = BoundedChannelFullMode.DropOldest,
        });

        _subscribers[subscriptionId] = channel;
        return new EventSubscription(subscriptionId, channel.Reader);
    }

    public void Unsubscribe(Guid subscriptionId)
    {
        if (_subscribers.TryRemove(subscriptionId, out var channel))
        {
            channel.Writer.TryComplete();
        }
    }

    public void Broadcast(WatcherEvent watcherEvent)
    {
        var payload = JsonSerializer.Serialize(watcherEvent, watcherEvent.GetType(), SerializerOptions);
        foreach (var subscriber in _subscribers.Values)
        {
            subscriber.Writer.TryWrite(payload);
        }
    }
}

public sealed record EventSubscription(Guid Id, ChannelReader<string> Reader);
