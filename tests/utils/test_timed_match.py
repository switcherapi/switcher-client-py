import time

from switcher_client.lib.utils.timed_match import TimedMatch

# Test data
OK_RE = "[a-z]"
OK_INPUT = "a"
NOK_RE = "^(([a-z])+.)+[A-Z]([a-z])+$"
NOK_INPUT = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"

COLD_TIME = 500  # ms
WARM_TIME = 50   # ms
TIMEOUT = 950    # ms - 50ms margin for worker thread to finish


def get_timer(start_time: float) -> float:
    """Calculate elapsed time in milliseconds."""
    return (time.time() - start_time) * 1000

class TestTimedMatch:
    """Timed-Match tests."""
    
    @classmethod
    def setup_class(cls):
        """Setup before all tests."""
        TimedMatch.initialize_worker()
    
    def setup_method(self):
        """Setup before each test."""
        TimedMatch.clear_blacklist()
        TimedMatch.set_max_blacklisted(50)
        TimedMatch.set_max_time_limit(1000)
    
    @classmethod
    def teardown_class(cls):
        """Cleanup after all tests."""
        TimedMatch.terminate_worker()
        # Give processes time to fully terminate
        time.sleep(0.2)

    def test_should_return_true(self):
        """Should return true for simple regex match."""

        result = TimedMatch.try_match([OK_RE], OK_INPUT)
        assert result is True

    def test_should_return_false_and_abort_processing(self):

        """Should return false and abort processing for ReDoS pattern."""
        result = TimedMatch.try_match([NOK_RE], NOK_INPUT)
        assert result is False

    def test_runs_stress_tests(self):
        """Run timing stress tests."""
        
        # First run - cold start
        timer = time.time()
        TimedMatch.try_match([OK_RE], OK_INPUT)
        elapsed = get_timer(timer)
        assert elapsed < COLD_TIME

        # ReDoS pattern should timeout
        timer = time.time()
        TimedMatch.try_match([NOK_RE], NOK_INPUT)
        elapsed = get_timer(timer)
        assert elapsed > TIMEOUT

        # Another good pattern should be fast
        timer = time.time()
        TimedMatch.try_match([OK_RE], OK_INPUT)
        elapsed = get_timer(timer)
        assert elapsed < COLD_TIME

        # Multiple runs should be fast (warm cache)
        for _ in range(10):
            timer = time.time()
            TimedMatch.try_match([OK_RE], OK_INPUT)
            elapsed = get_timer(timer)
            assert elapsed < WARM_TIME

    def test_should_rotate_blacklist(self):
        """Should rotate blacklist when max size is reached."""

        TimedMatch.set_max_blacklisted(1)

        # First ReDoS pattern times out
        timer = time.time()
        TimedMatch.try_match([NOK_RE], NOK_INPUT)
        elapsed = get_timer(timer)
        assert elapsed > TIMEOUT

        # Same pattern should be blacklisted (fast)
        timer = time.time()
        TimedMatch.try_match([NOK_RE], NOK_INPUT)
        elapsed = get_timer(timer)
        assert elapsed < WARM_TIME

        # New ReDoS pattern should timeout (replaces blacklist)
        timer = time.time()
        TimedMatch.try_match([NOK_RE], 'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb')
        elapsed = get_timer(timer)
        assert elapsed > TIMEOUT

        # New pattern should now be blacklisted (fast)
        timer = time.time()
        TimedMatch.try_match([NOK_RE], 'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb')
        elapsed = get_timer(timer)
        assert elapsed < WARM_TIME

    def test_should_capture_blacklisted_item_from_multiple_regex_options(self):
        """Should capture blacklisted item from multiple regex options."""

        TimedMatch.set_max_blacklisted(1)

        # First run with multiple patterns should timeout
        timer = time.time()
        TimedMatch.try_match([NOK_RE, OK_RE], NOK_INPUT)
        elapsed = get_timer(timer)
        assert elapsed > TIMEOUT

        # Blacklisted (inverted regex order should still work)
        timer = time.time()
        TimedMatch.try_match([OK_RE, NOK_RE], NOK_INPUT)
        elapsed = get_timer(timer)
        assert elapsed < WARM_TIME

    def test_should_capture_blacklisted_item_from_similar_inputs(self):
        """Should capture blacklisted item from similar inputs."""

        TimedMatch.set_max_blacklisted(1)

        # First ReDoS pattern
        timer = time.time()
        TimedMatch.try_match([NOK_RE, OK_RE], 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa')
        elapsed = get_timer(timer)
        assert elapsed > TIMEOUT

        # Blacklisted (input slightly different but contains the same evil segment)
        timer = time.time()
        TimedMatch.try_match([NOK_RE, OK_RE], 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaab')
        elapsed = get_timer(timer)
        assert elapsed < WARM_TIME

        # Same here
        timer = time.time()
        TimedMatch.try_match([NOK_RE, OK_RE], 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa')
        elapsed = get_timer(timer)
        assert elapsed < WARM_TIME

        # And here with inverted regex
        timer = time.time()
        TimedMatch.try_match([OK_RE, NOK_RE], 'aaaaaaaaaaaaaaaaaaaaaaa')
        elapsed = get_timer(timer)
        assert elapsed < WARM_TIME

    def test_should_reduce_worker_timer(self):
        """Should respect reduced worker timer setting."""
        
        TimedMatch.set_max_time_limit(500)

        timer = time.time()
        TimedMatch.try_match([NOK_RE], NOK_INPUT)
        elapsed = get_timer(timer)
        assert elapsed > 450
        assert elapsed < TIMEOUT
