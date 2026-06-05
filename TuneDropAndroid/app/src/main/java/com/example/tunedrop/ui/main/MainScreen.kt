package com.example.tunedrop.ui.main

import android.annotation.SuppressLint
import android.app.DownloadManager
import android.content.Context
import android.net.Uri
import android.os.Environment
import android.view.ViewGroup
import android.webkit.CookieManager
import android.webkit.URLUtil
import android.webkit.WebResourceError
import android.webkit.WebResourceRequest
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.Toast
import android.content.SharedPreferences
import androidx.compose.ui.platform.LocalContext
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.navigation3.runtime.NavKey

// Premium Color System
private val DeepSpace = Color(0xFF0D0B18)
private val MidnightViolet = Color(0xFF16122C)
private val NeonPink = Color(0xFFFF007F)
private val NeonViolet = Color(0xFF8A2BE2)
private val GlassBackground = Color(0xCC1A162B)
private val CardBorder = Color(0x33FF007F)

/**
 * Smart IP/URL utility that completes missing protocols and ports.
 * Example: "192.168.1.5" -> "http://192.168.1.5:5001"
 * Example: "tunedrop.web.app" -> "https://tunedrop.web.app"
 */
fun parseUrl(input: String): String {
  var url = input.trim()
  if (url.isEmpty()) return "http://10.0.2.2:5001"

  // Prepend protocol if missing
  if (!url.startsWith("http://") && !url.startsWith("https://")) {
    url = "http://$url"
  }

  try {
    val uri = Uri.parse(url)
    val host = uri.host ?: ""
    // If the host is a raw IP or localhost, and no port is provided, append default Flask port 5001
    val isIpOrLocalhost = host.matches(Regex("^[0-9.]+$")) || host == "localhost"
    if (isIpOrLocalhost && uri.port == -1) {
      url = "$url:5001"
    }
  } catch (e: Exception) {
    // Fallback if parsing fails
  }
  return url
}

@OptIn(ExperimentalMaterial3Api::class)
@SuppressLint("SetJavaScriptEnabled")
@Composable
fun MainScreen(
  onItemClick: (NavKey) -> Unit,
  modifier: Modifier = Modifier,
) {
  val context = LocalContext.current
  val prefs: SharedPreferences = remember { context.getSharedPreferences("tunedrop_prefs", Context.MODE_PRIVATE) }

  // Load saved connection URL, defaulting to local emulator URL
  var serverUrl by remember {
    mutableStateOf(prefs.getString("server_url", "http://10.0.2.2:5001") ?: "http://10.0.2.2:5001")
  }
  
  var isError by remember { mutableStateOf(false) }
  var showSettings by remember { mutableStateOf(false) }
  var tempUrlInput by remember { mutableStateOf(serverUrl) }
  
  var webViewRef by remember { mutableStateOf<WebView?>(null) }

  Box(modifier = Modifier.fillMaxSize().background(DeepSpace)) {
    // 1. Native WebView Wrapper
    AndroidView(
      modifier = Modifier.fillMaxSize(),
      factory = { ctx ->
        WebView(ctx).apply {
          webViewRef = this
          layoutParams = ViewGroup.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT,
            ViewGroup.LayoutParams.MATCH_PARENT
          )
          
          // Setup WebView Clients for safe local traffic & routing
          webViewClient = object : WebViewClient() {
            override fun shouldOverrideUrlLoading(view: WebView?, url: String?): Boolean {
              return false
            }

            override fun onReceivedError(
              view: WebView?,
              request: WebResourceRequest?,
              error: WebResourceError?
            ) {
              super.onReceivedError(view, request, error)
              // Only trigger error screen if the main web page fails to load
              if (request?.isForMainFrame == true) {
                isError = true
              }
            }

            override fun onPageFinished(view: WebView?, url: String?) {
              super.onPageFinished(view, url)
              if (url != null && url != "about:blank") {
                isError = false
              }
            }
          }

          // Performance and compatibility settings
          settings.apply {
            javaScriptEnabled = true
            domStorageEnabled = true
            databaseEnabled = true
            useWideViewPort = true
            loadWithOverviewMode = true
            cacheMode = WebSettings.LOAD_DEFAULT
          }

          // System DownloadManager hook
          setDownloadListener { url, userAgent, contentDisposition, mimetype, contentLength ->
            try {
              val request = DownloadManager.Request(Uri.parse(url)).apply {
                setMimeType(mimetype)
                val cookies = CookieManager.getInstance().getCookie(url)
                addRequestHeader("cookie", cookies)
                addRequestHeader("User-Agent", userAgent)
                setDescription("Downloading track from TuneDrop...")
                val guessedFileName = URLUtil.guessFileName(url, contentDisposition, mimetype)
                setTitle(guessedFileName)
                allowScanningByMediaScanner()
                setNotificationVisibility(DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED)
                setDestinationInExternalPublicDir(Environment.DIRECTORY_DOWNLOADS, guessedFileName)
              }
              val downloadManager = ctx.getSystemService(Context.DOWNLOAD_SERVICE) as DownloadManager
              downloadManager.enqueue(request)
              Toast.makeText(ctx, "Download started...", Toast.LENGTH_SHORT).show()
            } catch (e: Exception) {
              Toast.makeText(ctx, "Download failed: ${e.message}", Toast.LENGTH_LONG).show()
            }
          }
        }
      },
      update = { webView ->
        // Dynamically load the URL if it differs from the WebView's current URL
        if (webView.url != serverUrl) {
          webView.loadUrl(serverUrl)
        }
      }
    )

    // 2. Settings FAB (Subtle overlay trigger)
    Box(
      modifier = Modifier
        .align(Alignment.TopEnd)
        .padding(top = 48.dp, end = 16.dp)
    ) {
      IconButton(
        onClick = {
          tempUrlInput = serverUrl
          showSettings = true
        },
        modifier = Modifier
          .size(44.dp)
          .clip(CircleShape)
          .background(Color(0x6616122C))
          .border(1.dp, Color(0x33FFFFFF), CircleShape)
      ) {
        Icon(
          imageVector = Icons.Default.Settings,
          contentDescription = "Server Settings",
          tint = Color.White.copy(alpha = 0.8f)
        )
      }
    }

    // 3. Premium Glassmorphic Error/Setup Overlay
    AnimatedVisibility(
      visible = isError,
      enter = fadeIn(),
      exit = fadeOut()
    ) {
      Box(
        modifier = Modifier
          .fillMaxSize()
          .background(
            Brush.verticalGradient(
              colors = listOf(DeepSpace, MidnightViolet)
            )
          )
          .padding(24.dp),
        contentAlignment = Alignment.Center
      ) {
        Column(
          modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(24.dp))
            .background(GlassBackground)
            .border(1.dp, CardBorder, RoundedCornerShape(24.dp))
            .padding(24.dp)
            .verticalScroll(rememberScrollState()),
          horizontalAlignment = Alignment.CenterHorizontally
        ) {
          Text(
            text = "TuneDrop",
            fontSize = 32.sp,
            fontWeight = FontWeight.ExtraBold,
            color = NeonPink,
            textAlign = TextAlign.Center,
            modifier = Modifier.padding(bottom = 8.dp)
          )

          Text(
            text = "Cannot Connect to Server",
            fontSize = 20.sp,
            fontWeight = FontWeight.Bold,
            color = Color.White,
            textAlign = TextAlign.Center,
            modifier = Modifier.padding(bottom = 16.dp)
          )

          Text(
            text = "Please check that your computer is running the server script and your phone is connected to the same Wi-Fi network.",
            fontSize = 14.sp,
            color = Color.LightGray,
            textAlign = TextAlign.Center,
            lineHeight = 20.sp,
            modifier = Modifier.padding(bottom = 24.dp)
          )

          // Connection input field
          OutlinedTextField(
            value = tempUrlInput,
            onValueChange = { tempUrlInput = it },
            label = { Text("Server IP or URL", color = Color.Gray) },
            placeholder = { Text("e.g. 192.168.1.15", color = Color.DarkGray) },
            singleLine = true,
            colors = OutlinedTextFieldDefaults.colors(
              focusedTextColor = Color.White,
              unfocusedTextColor = Color.White,
              focusedBorderColor = NeonPink,
              unfocusedBorderColor = Color.Gray,
              focusedLabelColor = NeonPink,
              cursorColor = NeonPink
            ),
            keyboardOptions = KeyboardOptions(
              keyboardType = KeyboardType.Uri,
              imeAction = ImeAction.Done
            ),
            modifier = Modifier.fillMaxWidth().padding(bottom = 16.dp)
          )

          // Connect Button
          Button(
            onClick = {
              val parsed = parseUrl(tempUrlInput)
              serverUrl = parsed
              prefs.edit().putString("server_url", parsed).apply()
              isError = false
              webViewRef?.loadUrl(parsed)
            },
            colors = ButtonDefaults.buttonColors(containerColor = NeonPink),
            shape = RoundedCornerShape(12.dp),
            modifier = Modifier
              .fillMaxWidth()
              .height(50.dp)
          ) {
            Text(
              text = "Connect Now",
              fontSize = 16.sp,
              fontWeight = FontWeight.Bold,
              color = Color.White
            )
          }

          Spacer(modifier = Modifier.height(16.dp))

          // Preset options
          Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceEvenly
          ) {
            Text(
              text = "Emulator Default",
              fontSize = 12.sp,
              color = NeonViolet,
              fontWeight = FontWeight.SemiBold,
              modifier = Modifier
                .clickable {
                  tempUrlInput = "10.0.2.2"
                }
                .padding(8.dp)
            )

            Text(
              text = "Localhost Default",
              fontSize = 12.sp,
              color = NeonViolet,
              fontWeight = FontWeight.SemiBold,
              modifier = Modifier
                .clickable {
                  tempUrlInput = "127.0.0.1"
                }
                .padding(8.dp)
            )
          }
        }
      }
    }

    // 4. In-App Connection Settings Dialog
    if (showSettings) {
      AlertDialog(
        onDismissRequest = { showSettings = false },
        title = {
          Text(
            text = "TuneDrop Server Config",
            fontWeight = FontWeight.Bold,
            color = Color.White
          )
        },
        text = {
          Column {
            Text(
              text = "Enter your host computer's IP address or full domain name:",
              fontSize = 14.sp,
              color = Color.LightGray,
              modifier = Modifier.padding(bottom = 16.dp)
            )

            OutlinedTextField(
              value = tempUrlInput,
              onValueChange = { tempUrlInput = it },
              label = { Text("Server Address", color = Color.Gray) },
              placeholder = { Text("e.g. 192.168.1.15", color = Color.DarkGray) },
              singleLine = true,
              colors = OutlinedTextFieldDefaults.colors(
                focusedTextColor = Color.White,
                unfocusedTextColor = Color.White,
                focusedBorderColor = NeonPink,
                unfocusedBorderColor = Color.Gray,
                focusedLabelColor = NeonPink,
                cursorColor = NeonPink
              ),
              keyboardOptions = KeyboardOptions(
                keyboardType = KeyboardType.Uri,
                imeAction = ImeAction.Done
              ),
              modifier = Modifier.fillMaxWidth()
            )
          }
        },
        confirmButton = {
          Button(
            onClick = {
              val parsed = parseUrl(tempUrlInput)
              serverUrl = parsed
              prefs.edit().putString("server_url", parsed).apply()
              showSettings = false
              isError = false
              webViewRef?.loadUrl(parsed)
            },
            colors = ButtonDefaults.buttonColors(containerColor = NeonPink)
          ) {
            Text("Save & Connect", color = Color.White)
          }
        },
        dismissButton = {
          TextButton(onClick = { showSettings = false }) {
            Text("Cancel", color = Color.Gray)
          }
        },
        containerColor = MidnightViolet,
        shape = RoundedCornerShape(20.dp),
        modifier = Modifier.border(1.dp, CardBorder, RoundedCornerShape(20.dp))
      )
    }
  }
}
