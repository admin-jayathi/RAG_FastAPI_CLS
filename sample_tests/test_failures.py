import pytest
import requests
import time
import random

# ─────────────────────────────────────────────
# 1. PRODUCT_BUG — real assertion failure
#    The app returns wrong data. This always fails.
# ─────────────────────────────────────────────
def test_checkout_total_calculation():
    """Simulates a real product bug — wrong calculation in app."""
    item_price = 100
    quantity = 3
    expected_total = item_price * quantity  # 300
    actual_total = 250  # bug: app returns wrong total
    assert actual_total == expected_total, (
        f"Checkout total wrong: expected {expected_total}, got {actual_total}"
    )


def test_user_profile_returns_correct_name():
    """Simulates app returning wrong field."""
    api_response = {"id": 1, "username": "john_doe", "name": None}  # name is None — bug
    assert api_response["name"] is not None, "User profile name is null — product bug"


# ─────────────────────────────────────────────
# 2. FLAKY_TEST — timing / race condition
#    Fails intermittently (~40% of the time)
# ─────────────────────────────────────────────
def test_async_data_load():
    """Simulates a race condition — data not ready in time."""
    time.sleep(0.05)
    data_ready = random.random() > 0.4  # fails 40% of the time
    assert data_ready, "TimeoutException: async data did not load within threshold"


def test_concurrent_session_update():
    """Simulates a flaky session race condition."""
    result = random.choice([True, True, False, True, False])
    assert result, "ConcurrentModificationException: session updated by another thread"


# # ─────────────────────────────────────────────
# # 3. ENV_ISSUE — service unreachable
# #    Always fails because the service doesn't exist
# # ─────────────────────────────────────────────
# def test_payment_service_health():
#     """Simulates payment service being down."""
#     try:
#         resp = requests.get(
#             "http://payment-service.internal:9999/health",
#             timeout=2
#         )
#         assert resp.status_code == 200
#     except Exception:
#         raise AssertionError(
#             "HTTP 503: payment-service unreachable after 3 retries"
#         )


# def test_database_connection():
#     """Simulates DB being unreachable."""
#     try:
#         resp = requests.get(
#             "http://nonexistent-db.internal:5432/ping",
#             timeout=2
#         )
#         assert resp.status_code == 200
#     except Exception:
#         raise AssertionError(
#             "ConnectionRefusedError: could not connect to postgres at db.internal:5432"
#         )


# # ─────────────────────────────────────────────
# # 4. LOCATOR_BROKEN — UI element not found
# #    Simulates Selenium/Playwright selector failure
# # ─────────────────────────────────────────────
# def test_submit_button_click():
#     """Simulates a broken CSS locator after UI change."""
#     dom_snapshot = '<button id="btn-submit-v2">Submit</button>'
#     locator = "#submit-btn"  # old locator, no longer matches
#     assert locator in dom_snapshot, (
#         f"NoSuchElementException: element '{locator}' not found in DOM"
#     )


# def test_login_form_username_field():
#     """Simulates input field locator broken after redesign."""
#     dom_snapshot = '<input data-testid="email-input" />'
#     locator = "#username"  # old locator
#     assert locator in dom_snapshot, (
#         f"NoSuchElementException: '{locator}' not found — UI was redesigned"
#     )


# # ─────────────────────────────────────────────
# # 5. AUTH_ISSUE — token expired / 401
# # ─────────────────────────────────────────────
# def test_api_call_with_expired_token():
#     """Simulates calling an API with an expired JWT."""
#     response_status = 401  # server says unauthorized
#     assert response_status == 200, (
#         "AuthenticationError: JWT token expired — received 401 Unauthorized"
#     )


# def test_admin_dashboard_access():
#     """Simulates 403 Forbidden on protected route."""
#     response_status = 403
#     assert response_status == 200, (
#         "AuthorizationError: 403 Forbidden — user lacks admin role"
#     )


# # ─────────────────────────────────────────────
# # 6. TEST_DATA_ISSUE — missing/bad test data
# # ─────────────────────────────────────────────
# def test_order_history_for_user():
#     """Simulates test user having no orders in DB."""
#     test_user_orders = []  # test data was wiped
#     assert len(test_user_orders) > 0, (
#         "AssertionError: test user 'qa_user_01' has no orders — test data missing"
#     )


# def test_product_catalogue_not_empty():
#     """Simulates product table being empty in test env."""
#     products = []  # empty — test data issue
#     assert len(products) > 0, (
#         "AssertionError: product catalogue is empty in test environment"
#     )
