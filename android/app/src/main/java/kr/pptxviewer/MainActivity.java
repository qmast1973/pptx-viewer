package kr.pptxviewer;

import android.app.Activity;
import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.database.Cursor;
import android.net.Uri;
import android.os.Bundle;
import android.provider.OpenableColumns;
import android.view.View;
import android.view.ViewGroup;
import android.webkit.JavascriptInterface;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.FrameLayout;

import androidx.webkit.WebViewAssetLoader;

import java.io.InputStream;
import java.util.HashMap;
import java.util.Map;

/**
 * 웹앱(assets/www)을 https://appassets.androidplatform.net 주소로 띄우는 WebView 앱.
 * .pptx 를 '연결 프로그램'·'공유'로 받으면 그 파일을 /shared/file 로 웹앱에 넘겨 연다 (파일은 기기 밖으로 나가지 않음).
 */
public class MainActivity extends Activity {
    private static final String HOME = "https://appassets.androidplatform.net/assets/www/index.html";
    private static final int REQ_CHOOSE = 1;

    private WebView web;
    private FrameLayout root;
    private View customView;
    private WebChromeClient.CustomViewCallback customCb;
    private ValueCallback<Uri[]> chooser;
    private volatile Uri pendingUri;
    private volatile String pendingName;
    private boolean pageReady;

    @Override
    protected void onCreate(Bundle b) {
        super.onCreate(b);
        getWindow().setStatusBarColor(0xFF1F2227);
        getWindow().setNavigationBarColor(0xFF16181C);

        final WebViewAssetLoader loader = new WebViewAssetLoader.Builder()
                .addPathHandler("/assets/", new WebViewAssetLoader.AssetsPathHandler(this))
                .addPathHandler("/shared/", this::sharedFile)
                .build();

        root = new FrameLayout(this);
        web = new WebView(this);
        root.addView(web, new FrameLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));
        setContentView(root);

        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);            // IndexedDB(마지막 파일 기억) 포함
        s.setAllowFileAccess(false);
        s.setAllowContentAccess(false);
        s.setMediaPlaybackRequiresUserGesture(true);
        web.setBackgroundColor(0xFF16181C);

        web.addJavascriptInterface(new Bridge(), "AndroidApp");
        web.setWebViewClient(new WebViewClient() {
            @Override public WebResourceResponse shouldInterceptRequest(WebView v, WebResourceRequest r) {
                return loader.shouldInterceptRequest(r.getUrl());
            }
            @Override public boolean shouldOverrideUrlLoading(WebView v, WebResourceRequest r) {
                Uri u = r.getUrl();
                if ("appassets.androidplatform.net".equals(u.getHost())) return false;
                try { startActivity(new Intent(Intent.ACTION_VIEW, u)); } catch (ActivityNotFoundException ignored) { }
                return true;                     // 바깥 주소는 브라우저로
            }
            @Override public void onPageFinished(WebView v, String url) { pageReady = true; }
        });
        web.setWebChromeClient(new WebChromeClient() {
            @Override public boolean onShowFileChooser(WebView v, ValueCallback<Uri[]> cb, FileChooserParams p) {
                if (chooser != null) chooser.onReceiveValue(null);
                chooser = cb;
                try { startActivityForResult(p.createIntent(), REQ_CHOOSE); }
                catch (ActivityNotFoundException e) { chooser = null; return false; }
                return true;
            }
            @Override public void onShowCustomView(View view, CustomViewCallback cb) {   // 전체화면
                if (customView != null) { cb.onCustomViewHidden(); return; }
                customView = view; customCb = cb;
                root.addView(view, new FrameLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));
                web.setVisibility(View.GONE);
                view.setSystemUiVisibility(View.SYSTEM_UI_FLAG_FULLSCREEN | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION | View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY | View.SYSTEM_UI_FLAG_LAYOUT_STABLE);
            }
            @Override public void onHideCustomView() { hideCustom(); }
        });

        handleIntent(getIntent());
        web.loadUrl(HOME);
    }

    private void hideCustom() {
        if (customView == null) return;
        root.removeView(customView);
        customView = null;
        web.setVisibility(View.VISIBLE);
        if (customCb != null) customCb.onCustomViewHidden();
        customCb = null;
    }

    @Override protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        if (handleIntent(intent) && pageReady) web.evaluateJavascript("window.openFromApp&&window.openFromApp()", null);
    }

    /** 연결 프로그램(VIEW)·공유(SEND)로 받은 파일을 기억해 둔다. 받은 게 있으면 true */
    private boolean handleIntent(Intent i) {
        if (i == null) return false;
        Uri u = null;
        if (Intent.ACTION_VIEW.equals(i.getAction())) u = i.getData();
        else if (Intent.ACTION_SEND.equals(i.getAction())) u = i.getParcelableExtra(Intent.EXTRA_STREAM);
        if (u == null) return false;
        pendingUri = u;
        pendingName = displayName(u);
        return true;
    }

    private String displayName(Uri u) {
        String name = null;
        if ("content".equals(u.getScheme())) {
            try (Cursor c = getContentResolver().query(u, new String[]{OpenableColumns.DISPLAY_NAME}, null, null, null)) {
                if (c != null && c.moveToFirst()) name = c.getString(0);
            } catch (Exception ignored) { }
        }
        if (name == null || name.isEmpty()) name = u.getLastPathSegment();
        if (name == null || name.isEmpty()) name = "공유받은 파일.pptx";
        return name;
    }

    /** 웹앱이 fetch("/shared/file") 로 받아 가는 파일 */
    private WebResourceResponse sharedFile(String path) {
        Uri u = pendingUri;
        if (u == null) return new WebResourceResponse("text/plain", "utf-8", 404, "Not Found", new HashMap<>(), null);
        try {
            InputStream in = getContentResolver().openInputStream(u);
            Map<String, String> h = new HashMap<>();
            h.put("Cache-Control", "no-store");
            return new WebResourceResponse("application/octet-stream", null, 200, "OK", h, in);
        } catch (Exception e) {
            return new WebResourceResponse("text/plain", "utf-8", 500, "Error", new HashMap<>(), null);
        }
    }

    private class Bridge {
        /** 받아 둔 파일 이름을 돌려주고 비움 (없으면 빈 문자열). 파일 내용은 /shared/file 로 받는다 */
        @JavascriptInterface public String takePending() {
            String n = pendingName;
            pendingName = null;
            return n == null ? "" : n;
        }
    }

    @Override protected void onActivityResult(int req, int res, Intent data) {
        if (req == REQ_CHOOSE && chooser != null) {
            chooser.onReceiveValue(WebChromeClient.FileChooserParams.parseResult(res, data));
            chooser = null;
            return;
        }
        super.onActivityResult(req, res, data);
    }

    @Override public void onBackPressed() {
        if (customView != null) hideCustom();
        else super.onBackPressed();
    }

    @Override protected void onDestroy() {
        if (web != null) { root.removeAllViews(); web.destroy(); }
        super.onDestroy();
    }
}
