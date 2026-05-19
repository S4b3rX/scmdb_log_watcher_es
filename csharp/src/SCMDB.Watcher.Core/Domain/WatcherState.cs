namespace SCMDB.Watcher.Core.Domain;

public sealed class WatcherState
{
    private const int MaxRecentLifecycleEvents = 32;
    private readonly object _sync = new();
    private readonly Dictionary<string, MissionEntry> _guidMap = new(StringComparer.Ordinal);
    private readonly Dictionary<string, ActiveMission> _active = new(StringComparer.Ordinal);
    private readonly Queue<MissionLifecycleEvent> _recentLifecycle = new();

    public void Reset()
    {
        lock (_sync)
        {
            _guidMap.Clear();
            _active.Clear();
            _recentLifecycle.Clear();
        }
    }

    public void RecordMarker(string guid, string generator, string contract)
    {
        lock (_sync)
        {
            if (!_guidMap.ContainsKey(guid))
            {
                _guidMap[guid] = new MissionEntry(contract, generator);
            }
        }
    }

    public ActiveMission? RecordAccepted(string guid, double ts)
    {
        lock (_sync)
        {
            if (!_guidMap.TryGetValue(guid, out var entry))
            {
                return null;
            }

            var activeMission = new ActiveMission(guid, entry.DebugName, entry.Generator, ts);
            _active[guid] = activeMission;
            EnqueueLifecycle(new MissionLifecycleEvent("accept", guid, entry.DebugName, ts));
            return activeMission;
        }
    }

    public ActiveMission? RecordEnd(string guid, string completion, double ts)
    {
        lock (_sync)
        {
            _active.TryGetValue(guid, out var activeMission);
            _active.Remove(guid);

            if (completion == "Complete")
            {
                var debugName = activeMission?.DebugName
                    ?? (_guidMap.TryGetValue(guid, out var entry) ? entry.DebugName : "?");
                EnqueueLifecycle(new MissionLifecycleEvent("complete", guid, debugName, ts));
            }

            return activeMission;
        }
    }

    public MissionEntry? GetMissionEntry(string guid)
    {
        lock (_sync)
        {
            return _guidMap.TryGetValue(guid, out var entry) ? entry : null;
        }
    }

    public MissionLifecycleEvent? CorrelateBlueprint(double ts, double correlationWindowSeconds = 5.0d)
    {
        lock (_sync)
        {
            MissionLifecycleEvent? best = null;
            var bestDelta = correlationWindowSeconds + 1.0d;

            foreach (var lifecycleEvent in _recentLifecycle)
            {
                var delta = ts - lifecycleEvent.Ts;
                if (delta >= 0.0d && delta <= correlationWindowSeconds && delta < bestDelta)
                {
                    best = lifecycleEvent;
                    bestDelta = delta;
                }
            }

            return best;
        }
    }

    public IReadOnlyList<ActiveMission> SnapshotActive()
    {
        lock (_sync)
        {
            return _active.Values.ToList();
        }
    }

    private void EnqueueLifecycle(MissionLifecycleEvent lifecycleEvent)
    {
        _recentLifecycle.Enqueue(lifecycleEvent);
        while (_recentLifecycle.Count > MaxRecentLifecycleEvents)
        {
            _recentLifecycle.Dequeue();
        }
    }
}
