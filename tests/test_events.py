from astra.game.events import EventBus


def test_event_bus_emit_and_drain():
    bus = EventBus()
    bus.emit("tick_done", amount=1, day=1)
    assert bus.peek() == [{"type": "tick_done", "amount": 1, "day": 1}]
    assert bus.drain() == [{"type": "tick_done", "amount": 1, "day": 1}]
    assert bus.peek() == []
