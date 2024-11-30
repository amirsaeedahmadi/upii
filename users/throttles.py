from rest_framework.throttling import UserRateThrottle

from utils.tokens import get_otp_expiry


class OTPRateThrottle(UserRateThrottle):
    def get_rate(self):
        return f"{get_otp_expiry()}/second"
