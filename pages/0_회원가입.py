# -*- coding: utf-8 -*-
"""회원가입 - 아이디 중복 확인, 비밀번호 확인"""
import streamlit as st

from core import ensure_data_dir, init_db, inject_custom_css
from core.repositories.users_repo import username_exists
from core.services.auth_service import register

REGISTER_CSS = """
<style>
.register-container { max-width: 400px !important; margin: 2rem auto !important; padding: 1.5rem !important; }
.register-title { font-size: 1.3rem !important; font-weight: 600 !important; margin-bottom: 1rem !important; }
.register-footer { margin-top: 1.5rem !important; font-size: 0.85rem !important; }
</style>
"""


def main() -> None:
    st.set_page_config(page_title="회원가입 - NHK Easy Reader", layout="centered")
    inject_custom_css()
    st.markdown(REGISTER_CSS, unsafe_allow_html=True)
    ensure_data_dir()
    init_db()

    st.markdown('<div class="register-container">', unsafe_allow_html=True)
    st.markdown('<p class="register-title">📝 회원가입</p>', unsafe_allow_html=True)

    with st.form("register_form", clear_on_submit=True):
        user_id = st.text_input("아이디", placeholder="2자 이상", key="reg_id")
        check_btn = st.form_submit_button("아이디 중복 확인")
        if check_btn:
            if not (user_id or "").strip():
                st.warning("아이디를 입력하세요.")
            elif username_exists(user_id):
                st.error("이미 사용 중인 아이디입니다.")
            else:
                st.success("사용 가능한 아이디입니다.")
                st.session_state["reg_id_checked"] = user_id.strip().lower()

        password = st.text_input("비밀번호", type="password", placeholder="4자 이상", key="reg_pw")
        password_confirm = st.text_input("비밀번호 확인", type="password", placeholder="비밀번호 다시 입력", key="reg_pw2")
        submitted = st.form_submit_button("가입하기")

        if submitted:
            uid = (user_id or "").strip()
            if not uid:
                st.error("아이디를 입력하세요.")
            elif len(uid) < 2:
                st.error("아이디는 2자 이상이어야 합니다.")
            elif username_exists(uid):
                st.error("이미 사용 중인 아이디입니다.")
            elif not password:
                st.error("비밀번호를 입력하세요.")
            elif len(password) < 4:
                st.error("비밀번호는 4자 이상이어야 합니다.")
            elif password != password_confirm:
                st.error("비밀번호가 일치하지 않습니다.")
            else:
                ok, msg = register(uid, password)
                if ok:
                    st.session_state["reg_success"] = True
                    st.rerun()
                else:
                    st.error(msg)

    # 가입 성공 시 (form 밖에서 버튼 표시)
    if st.session_state.get("reg_success"):
        st.success("회원가입이 완료되었습니다. 로그인 페이지에서 로그인하세요.")
        if st.button("로그인으로 이동"):
            del st.session_state["reg_success"]
            st.switch_page("app.py")
        st.stop()

    st.markdown('<p class="register-footer">이미 계정이 있으신가요? </p>', unsafe_allow_html=True)
    if st.button("로그인", key="go_login"):
        st.switch_page("app.py")
    st.markdown("</div>", unsafe_allow_html=True)


main()
