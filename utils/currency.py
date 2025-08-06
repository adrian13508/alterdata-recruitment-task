from decimal import Decimal

from django.conf import settings


def convert_to_pln(amount, currency):
    """
    Convert amount from given currency to PLN using configured exchange rates

    Args:
        amount (Decimal): Amount to convert
        currency (str): Source currency code (EUR, USD, PLN)

    Returns:
        Decimal: Amount in PLN
    """
    if currency == 'PLN':
        return Decimal(str(amount))

    exchange_rates = settings.CURRENCY_EXCHANGE_RATES

    if currency not in exchange_rates:
        raise ValueError(f"Unsupported currency: {currency}")

    rate = Decimal(str(exchange_rates[currency]))
    return Decimal(str(amount)) * rate


def get_supported_currencies():
    """Return list of supported currencies"""
    return list(settings.CURRENCY_EXCHANGE_RATES.keys())
