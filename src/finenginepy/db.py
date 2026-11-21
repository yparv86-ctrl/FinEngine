import pandas as pd
import streamlit as st
from supabase import create_client, Client

@st.cache_resource
def init_connection() -> Client:
    raw_url = str(st.secrets["SUPABASE_URL"]).strip().strip('"').strip("'")
    key = str(st.secrets["SUPABASE_KEY"]).strip().strip('"').strip("'")

    if "supabase.com/dashboard/project/" in raw_url:
        project_id = raw_url.split("supabase.com/dashboard/project/")[-1].split("/")[0].split("?")[0]
        url = f"https://{project_id}.supabase.co"
    elif not raw_url.startswith(("http://", "https://")):
        if ".supabase.co" in raw_url:
            url = f"https://{raw_url}"
        else:
            url = f"https://{raw_url}.supabase.co"
    else:
        url = raw_url.rstrip("/")

    return create_client(url, key)

supabase: Client = init_connection()

def init_db():
    pass

def _get_authed_table():
    """Attaches the current user's JWT token so Supabase RLS authorizes the request."""
    session = st.session_state.get("supabase_session")
    if session and getattr(session, "access_token", None):
        supabase.postgrest.auth(session.access_token)
    return supabase.table("audit_ledger")

def require_auth():
    """Renders the login/signup screen if unauthenticated, or a sidebar account badge if logged in."""
    if "user" not in st.session_state or st.session_state["user"] is None:
        col1, col2, col3 = st.columns([1, 1.4, 1])
        with col2:
            st.subheader("Institutional Access Portal")
            auth_mode = st.tabs(["Sign In", "Create Account"])

            with auth_mode[0]:
                email = st.text_input("Work Email", key="login_email").strip()
                password = st.text_input("Password", type="password", key="login_password")
                if st.button("Sign In", type="primary", use_container_width=True, key="login_btn"):
                    if not email or not password:
                        st.warning("Please enter both your email and password.")
                    else:
                        try:
                            res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                            st.session_state["user"] = res.user
                            st.session_state["supabase_session"] = res.session
                            st.rerun()
                        except Exception as e:
                            st.error(f"Authentication failed: {e}")

            with auth_mode[1]:
                new_email = st.text_input("Work Email", key="signup_email").strip()
                new_password = st.text_input("Password (min 6 characters)", type="password", key="signup_password")
                if st.button("Create Account", type="primary", use_container_width=True, key="signup_btn"):
                    if not new_email or not new_password:
                        st.warning("Please type your email and a password (at least 6 characters).")
                    else:
                        try:
                            res = supabase.auth.sign_up({"email": new_email, "password": new_password})
                            if res.session:
                                st.session_state["user"] = res.user
                                st.session_state["supabase_session"] = res.session
                                st.rerun()
                            else:
                                st.success("Account created! Switch to the Sign In tab to log in.")
                        except Exception as e:
                            st.error(f"Sign-up failed: {e}")
        st.stop()

    # Render logged-in user controls in the sidebar
    user_email = st.session_state["user"].email
    st.sidebar.caption(f"Logged in as: **{user_email}**")
    if st.sidebar.button("Sign Out", use_container_width=True):
        try:
            supabase.auth.sign_out()
        except Exception:
            pass
        st.session_state["user"] = None
        st.session_state["supabase_session"] = None
        st.rerun()
    st.sidebar.divider()

def log_valuation(ticker, model_type, market_price, intrinsic_value, discount_rate):
    user_id = st.session_state["user"].id
    data = {
        "user_id": user_id,
        "ticker": ticker,
        "model_type": model_type,
        "market_price": float(market_price),
        "intrinsic_value": float(intrinsic_value),
        "discount_rate": float(discount_rate)
    }
    _get_authed_table().insert(data).execute()

def get_valuation_history():
    user_id = st.session_state["user"].id
    response = (
        _get_authed_table()
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )
    data = response.data

    if not data:
        return pd.DataFrame()

    df = pd.DataFrame(data)
    df = df.rename(columns={"created_at": "timestamp"})
    df["spread_pct"] = ((df["intrinsic_value"] - df["market_price"]) / df["market_price"]) * 100
    df["verdict"] = df.apply(
        lambda row: "UNDERVALUED" if row["intrinsic_value"] > row["market_price"] else "OVERVALUED",
        axis=1
    )
    df["timestamp"] = pd.to_datetime(df["timestamp"]).dt.strftime("%Y-%m-%d %H:%M")

    return df[["timestamp", "ticker", "model_type", "market_price", "intrinsic_value", "discount_rate", "spread_pct", "verdict"]]

def clear_valuation_history():
    user_id = st.session_state["user"].id
    _get_authed_table().delete().eq("user_id", user_id).execute()