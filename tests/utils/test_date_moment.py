import pytest

from datetime import datetime
from switcher_client.lib.utils.date_moment import DateMoment

class TestDateMoment:
    """ DateMoment tests """
    
    def test_should_add_1_second_to_date(self):
        """ Should add 1 second to date """
        today_moment = DateMoment(datetime.now().replace(hour=10, minute=0, second=0, microsecond=0))
        before_adding = today_moment.get_date().second
        after_adding = today_moment.add(1, 's').get_date().second
        diff = after_adding - before_adding
        assert diff == 1
    
    def test_should_add_1_minute_to_date(self):
        """ Should add 1 minute to date """
        today_moment = DateMoment(datetime.now().replace(hour=10, minute=0, second=0, microsecond=0))
        before_adding = today_moment.get_date().minute
        after_adding = today_moment.add(1, 'm').get_date().minute
        assert (after_adding - before_adding) == 1
    
    def test_should_add_1_hour_to_date(self):
        """ Should add 1 hour to date """
        today_moment = DateMoment(datetime.now().replace(hour=10, minute=0, second=0, microsecond=0))
        before_adding = today_moment.get_date().hour
        after_adding = today_moment.add(1, 'h').get_date().hour
        assert (after_adding - before_adding) == 1
    
    def test_should_return_error_for_using_not_compatible_unit(self):
        """ Should return error for using not compatible unit """
        today_moment = DateMoment(datetime.now().replace(hour=10, minute=0, second=0, microsecond=0))
        with pytest.raises(ValueError) as excinfo:
            today_moment.add(1, 'x')
        assert 'Unit x not compatible - try [s, m or h]' in str(excinfo.value)
