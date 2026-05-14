# -*- coding: utf-8 -*-
"""PWA manifest/Service Worker 주입 (경량 모듈 - streamlit만 의존)"""
import streamlit as st

from .config import APP_PWA_META_TITLE


def inject_pwa_manifest() -> None:
    """PWA manifest 링크 주입 (홈 화면 추가용)"""
    meta_title = APP_PWA_META_TITLE.replace('"', "&quot;")
    st.markdown(
        '<link rel="manifest" href="/app/static/manifest.json">'
        '<link rel="apple-touch-icon" href="/app/static/apple-touch-icon.png">'
        '<meta name="theme-color" content="#3b82f6">'
        '<meta name="apple-mobile-web-app-capable" content="yes">'
        '<meta name="apple-mobile-web-app-status-bar-style" content="default">'
        f'<meta name="apple-mobile-web-app-title" content="{meta_title}">',
        unsafe_allow_html=True,
    )
    st.markdown(
        r"""
<script>
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/app/static/sw.js')
    .then(function(reg) { console.log('SW registered'); })
    .catch(function(err) { console.log('SW reg failed:', err); });
}
</script>
""",
        unsafe_allow_html=True,
    )
