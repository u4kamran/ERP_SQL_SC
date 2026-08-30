from app.services.otp_sms_control_service import effective_allowed


def test_effective_matrix():
    cases = [
        (False, True, True, False, False),
        (True, False, True, False, True),
        (True, True, False, True, False),
        (True, True, True, True, True),
        (False, False, False, False, False),
        (False, True, False, False, False),
        (True, False, False, False, False),
    ]
    for master, web, mobile, web_eff, mobile_eff in cases:
        assert effective_allowed(master_enabled=master, channel_enabled=web) is web_eff
        assert effective_allowed(master_enabled=master, channel_enabled=mobile) is mobile_eff
