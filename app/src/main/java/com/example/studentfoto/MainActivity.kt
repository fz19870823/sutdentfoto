package com.example.studentfoto

import android.Manifest
import android.app.Activity
import android.content.Context
import android.content.pm.PackageManager
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Matrix
import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.hardware.SensorManager
import android.media.ExifInterface
import android.net.Uri
import android.net.wifi.WifiInfo
import android.net.wifi.WifiManager
import android.os.Bundle
import android.provider.MediaStore
import android.util.Log
import android.view.WindowManager
import androidx.appcompat.app.AppCompatActivity
import androidx.camera.core.CameraSelector
import androidx.camera.core.ImageCapture
import androidx.camera.core.ImageCaptureException
import androidx.camera.core.Preview
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.view.PreviewView
import android.widget.Button
import android.widget.TextView
import android.widget.Toast
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import java.io.File
import java.text.SimpleDateFormat
import java.util.*
import java.util.concurrent.ExecutorService
import java.util.concurrent.Executors
import kotlin.properties.Delegates
import java.io.IOException
import java.io.ByteArrayOutputStream
import java.net.ServerSocket
import java.net.Socket
import android.content.ContentValues
import androidx.core.os.bundleOf
import com.example.studentfoto.R  // 导入 R 类以解决 layout 和 id 的引用问题

class MainActivity : AppCompatActivity(), SensorEventListener {

    private lateinit var cameraExecutor: ExecutorService
    private var imageCapture: ImageCapture? = null
    private var _ipAddress by Delegates.notNull<String>()
    private val ipAddress: String get() = _ipAddress
    private lateinit var serverSocket: ServerSocket
    private var clientSocket: Socket? = null
    private var isServerRunning = false
    private var connectedPcInfo: String? = null

    // 重力感应相关
    private lateinit var sensorManager: SensorManager
    private var accelerometer: Sensor? = null
    private var currentOrientation = 0 // 0=竖屏, 90=左横屏, 180=倒立, 270=右横屏

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        // 保持屏幕常亮，防止息屏
        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        Log.d("MainActivity", "Screen keep on enabled - 屏幕保持常亮已启用")

        // 初始化执行器服务
        cameraExecutor = Executors.newSingleThreadExecutor()

        // 获取手机IP地址
        _ipAddress = getIPAddress()
        Log.d("MainActivity", "Device IP Address: $ipAddress")

        // 显示IP地址
        findViewById<TextView>(R.id.ip_address_text).text = "IP Address: $ipAddress"

        // 初始化连接状态显示
        updateConnectionStatus("等待PC连接...")

        // 初始化重力感应
        initSensor()

        // 请求相机权限
        if (allPermissionsGranted()) {
            startCamera()
        } else {
            ActivityCompat.requestPermissions(
                this, REQUIRED_PERMISSIONS, REQUEST_CODE_PERMISSIONS
            )
        }

        // 设置拍照按钮点击事件
        findViewById<Button>(R.id.capture_button).setOnClickListener { takePhoto() }

        // 启动服务器监听电脑端控制
        startServer()
    }

    private fun startCamera() {
        val cameraProviderFuture = ProcessCameraProvider.getInstance(this@MainActivity)

        cameraProviderFuture.addListener({
            val cameraProvider: ProcessCameraProvider = cameraProviderFuture.get()
            val preview = Preview.Builder().build().also {
                it.setSurfaceProvider(findViewById<PreviewView>(R.id.viewFinder).surfaceProvider)
            }

            imageCapture = ImageCapture.Builder().build()

            val cameraSelector = CameraSelector.DEFAULT_BACK_CAMERA

            try {
                cameraProvider.unbindAll()
                cameraProvider.bindToLifecycle(
                    this@MainActivity, cameraSelector, preview, imageCapture
                )
            } catch (exc: Exception) {
                Log.e("MainActivity", "Use case binding failed", exc)
            }
        }, ContextCompat.getMainExecutor(this@MainActivity))
    }

    private fun takePhoto() {
        val imageCapture = imageCapture ?: return

        val name = SimpleDateFormat(FILENAME_FORMAT, Locale.US)
            .format(System.currentTimeMillis())
        val contentValues = ContentValues().apply {
            put(MediaStore.MediaColumns.DISPLAY_NAME, name)
            put(MediaStore.MediaColumns.MIME_TYPE, "image/jpeg")
            put(MediaStore.Images.Media.RELATIVE_PATH, "Pictures/CameraX-Image")
        }

        val outputOptions = ImageCapture.OutputFileOptions
            .Builder(contentResolver,
                MediaStore.Images.Media.EXTERNAL_CONTENT_URI,
                contentValues)
            .build()

        imageCapture.takePicture(
            outputOptions,
            ContextCompat.getMainExecutor(this@MainActivity),
            object : ImageCapture.OnImageSavedCallback {
                override fun onImageSaved(output: ImageCapture.OutputFileResults) {
                    val savedUri = output.savedUri ?: return
                    Log.d("MainActivity", "Photo capture succeeded: $savedUri")

                    // 显示拍照成功提示（已经在主线程中）
                    Toast.makeText(this@MainActivity, "拍照成功！", Toast.LENGTH_SHORT).show()

                    // 通知PC端拍照完成
                    notifyPhotoTaken(savedUri)
                }

                override fun onError(exception: ImageCaptureException) {
                    Log.e("MainActivity", "Photo capture failed: ${exception.message}", exception)
                    Toast.makeText(this@MainActivity, "拍照失败: ${exception.message}", Toast.LENGTH_SHORT).show()

                    // 在后台线程中通知PC端拍照失败
                    Thread {
                        clientSocket?.let { socket ->
                            try {
                                val outputStream = socket.getOutputStream()
                                val message = "ERROR:拍照失败 - ${exception.message}"
                                outputStream.write(message.toByteArray())
                                outputStream.flush()
                            } catch (e: IOException) {
                                Log.e("MainActivity", "Failed to notify PC about error: ${e.message}")
                            }
                        }
                    }.start()
                }
            })
    }

    private fun notifyPhotoTaken(uri: Uri) {
        // 在后台线程中发送照片到PC端
        Thread {
            clientSocket?.let { socket ->
                try {
                    sendPhotoToPC(socket, uri)
                } catch (e: Exception) {
                    Log.e("MainActivity", "Failed to send photo to PC: ${e.message}")
                }
            }
        }.start()
    }

    private fun sendPhotoToPC(socket: Socket, uri: Uri) {
        try {
            val outputStream = socket.getOutputStream()

            // 首先发送拍照完成通知
            val notifyMessage = "PHOTO_TAKEN:$uri\n"
            outputStream.write(notifyMessage.toByteArray())
            outputStream.flush()
            Log.d("MainActivity", "Notified PC: $notifyMessage")

            // 读取并处理照片数据
            val inputStream = contentResolver.openInputStream(uri)
            inputStream?.use { input ->
                val originalPhotoBytes = input.readBytes()
                Log.d("MainActivity", "Original photo size: ${originalPhotoBytes.size} bytes")

                // 根据当前方向旋转照片（物理旋转）
                val rotatedPhotoBytes = rotatePhotoToCorrectOrientation(originalPhotoBytes, currentOrientation)
                Log.d("MainActivity", "Rotated photo size: ${rotatedPhotoBytes.size} bytes, orientation: $currentOrientation°")

                // 发送照片数据头信息
                val photoHeader = "PHOTO_DATA:${rotatedPhotoBytes.size}\n"
                outputStream.write(photoHeader.toByteArray())
                outputStream.flush()
                Log.d("MainActivity", "Sending photo header: ${rotatedPhotoBytes.size} bytes")

                // 等待一小段时间确保头信息被完全发送
                Thread.sleep(50)

                // 发送照片数据（纯二进制，不添加任何文本）
                outputStream.write(rotatedPhotoBytes)
                outputStream.flush()
                Log.d("MainActivity", "Photo binary data sent: ${rotatedPhotoBytes.size} bytes")

                // 等待一小段时间确保照片数据被完全发送
                Thread.sleep(50)

                // 发送结束标记
                val endMarker = "PHOTO_END\n"
                outputStream.write(endMarker.toByteArray())
                outputStream.flush()
                Log.d("MainActivity", "Photo end marker sent")

                Log.d("MainActivity", "Photo sent successfully to PC")
            } ?: run {
                Log.e("MainActivity", "Failed to open photo input stream")
            }

        } catch (e: IOException) {
            Log.e("MainActivity", "Failed to send photo: ${e.message}")
        }
    }

    private fun rotatePhotoToCorrectOrientation(photoBytes: ByteArray, orientation: Int): ByteArray {
        return try {
            // 解码原始图片
            val originalBitmap = BitmapFactory.decodeByteArray(photoBytes, 0, photoBytes.size)
            if (originalBitmap == null) {
                Log.e("MainActivity", "Failed to decode bitmap")
                return photoBytes
            }

            Log.d("MainActivity", "Original bitmap size: ${originalBitmap.width}x${originalBitmap.height}")

            // 统一对所有方向进行90度顺时针修正（因为系统问题导致所有照片都左旋了90度）
            Log.d("MainActivity", "Applying universal 90° clockwise correction for orientation: $orientation°")

            val matrix = Matrix()
            when (orientation) {
                0 -> {
                    // 竖屏：原来0°，现在修正为+90°
                    matrix.postRotate(90f)
                    Log.d("MainActivity", "Portrait: rotating +90° (0° + 90° correction)")
                }
                90 -> {
                    // 左横屏：原来需要+90°，现在修正为+180°
                    matrix.postRotate(180f)
                    Log.d("MainActivity", "Left landscape: rotating +180° (90° + 90° correction)")
                }
                180 -> {
                    // 倒立：原来需要180°，现在修正为+270°
                    matrix.postRotate(270f)
                    Log.d("MainActivity", "Upside down: rotating +270° (180° + 90° correction)")
                }
                270 -> {
                    // 右横屏：原来需要-90°，现在修正为0°（不旋转）
                    matrix.postRotate(0f)
                    Log.d("MainActivity", "Right landscape: no rotation (-90° + 90° correction = 0°)")
                }
            }

            // 应用旋转矩阵
            val finalBitmap = if (orientation == 270) {
                // 右横屏不需要旋转，直接使用原图
                originalBitmap
            } else {
                // 其他方向都需要旋转
                val rotatedBitmap = Bitmap.createBitmap(
                    originalBitmap, 0, 0,
                    originalBitmap.width, originalBitmap.height,
                    matrix, true
                )
                Log.d("MainActivity", "Rotated bitmap size: ${rotatedBitmap.width}x${rotatedBitmap.height}")
                rotatedBitmap
            }

            // 将图片转换为标准JPEG字节数组
            val outputStream = java.io.ByteArrayOutputStream()
            finalBitmap.compress(Bitmap.CompressFormat.JPEG, 90, outputStream)
            val processedBytes = outputStream.toByteArray()

            // 清理资源
            originalBitmap.recycle()
            if (finalBitmap != originalBitmap) {
                finalBitmap.recycle()
            }
            outputStream.close()

            Log.d("MainActivity", "Photo rotation completed successfully")
            processedBytes

        } catch (e: Exception) {
            Log.e("MainActivity", "Failed to rotate photo: ${e.message}")
            // 如果旋转失败，返回原始数据
            photoBytes
        }
    }

    private fun allPermissionsGranted() = REQUIRED_PERMISSIONS.all {
        ContextCompat.checkSelfPermission(
            baseContext, it
        ) == PackageManager.PERMISSION_GRANTED
    }

    override fun onRequestPermissionsResult(
        requestCode: Int, permissions: Array<String>, grantResults: IntArray
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == REQUEST_CODE_PERMISSIONS) {
            if (allPermissionsGranted()) {
                startCamera()
            } else {
                Toast.makeText(this, "权限被拒绝", Toast.LENGTH_SHORT).show()
                finish()
            }
        }
    }

    override fun onPause() {
        super.onPause()
        Log.d("MainActivity", "Activity paused")

        // 注销传感器监听器
        accelerometer?.let {
            sensorManager.unregisterListener(this, it)
            Log.d("MainActivity", "重力感应器监听已停止")
        }
    }

    override fun onResume() {
        super.onResume()
        Log.d("MainActivity", "Activity resumed")

        // 注册传感器监听器
        accelerometer?.let {
            sensorManager.registerListener(this, it, SensorManager.SENSOR_DELAY_NORMAL)
            Log.d("MainActivity", "重力感应器监听已启动")
        }

        // 确保相机在恢复时重新初始化
        if (allPermissionsGranted()) {
            startCamera()
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        Log.d("MainActivity", "Activity destroying")

        // 清除屏幕常亮标志
        window.clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        Log.d("MainActivity", "Screen keep on disabled - 屏幕常亮已关闭")

        // 注销传感器监听器
        accelerometer?.let {
            sensorManager.unregisterListener(this, it)
            Log.d("MainActivity", "重力感应器监听已注销")
        }

        cameraExecutor.shutdown()
        isServerRunning = false
        try {
            clientSocket?.close()
            if (::serverSocket.isInitialized) {
                serverSocket.close()
            }
        } catch (e: IOException) {
            e.printStackTrace()
        }
    }

    companion object {
        private const val TAG = "CameraXApp"
        private const val FILENAME_FORMAT = "yyyy-MM-dd-HH-mm-ss-SSS"
        private const val REQUEST_CODE_PERMISSIONS = 10
        private val REQUIRED_PERMISSIONS = arrayOf(
            Manifest.permission.CAMERA,
            Manifest.permission.WRITE_EXTERNAL_STORAGE
        )
    }

    private fun updateConnectionStatus(status: String) {
        runOnUiThread {
            findViewById<TextView>(R.id.connection_status_text).text = "📱 $status"
        }
    }

    private fun updateOrientationDisplay(orientationText: String) {
        runOnUiThread {
            findViewById<TextView>(R.id.orientation_status_text).text = "🧭 方向: $orientationText"
        }
    }

    private fun initSensor() {
        sensorManager = getSystemService(Context.SENSOR_SERVICE) as SensorManager
        accelerometer = sensorManager.getDefaultSensor(Sensor.TYPE_ACCELEROMETER)

        if (accelerometer != null) {
            Log.d("MainActivity", "重力感应器初始化成功")
        } else {
            Log.w("MainActivity", "设备不支持重力感应器")
        }
    }

    override fun onSensorChanged(event: SensorEvent?) {
        if (event?.sensor?.type == Sensor.TYPE_ACCELEROMETER) {
            val x = event.values[0]
            val y = event.values[1]
            val z = event.values[2]

            // 计算设备方向
            val newOrientation = calculateOrientation(x, y, z)

            if (newOrientation != currentOrientation) {
                currentOrientation = newOrientation
                val orientationText = when (currentOrientation) {
                    0 -> "竖屏"
                    90 -> "左横屏"
                    180 -> "倒立"
                    270 -> "右横屏"
                    else -> "未知"
                }
                Log.d("MainActivity", "设备方向变化: $orientationText ($currentOrientation°)")

                // 更新界面显示
                updateOrientationDisplay(orientationText)

                // 更新相机方向
                updateCameraOrientation()
            }
        }
    }

    override fun onAccuracyChanged(sensor: Sensor?, accuracy: Int) {
        // 传感器精度变化时的处理（通常不需要特殊处理）
    }

    private fun calculateOrientation(x: Float, y: Float, z: Float): Int {
        // 使用重力加速度值计算设备方向
        val threshold = 5.0f // 阈值，避免频繁切换

        return when {
            y > threshold -> 0    // 竖屏（正常）
            x > threshold -> 270  // 右横屏
            y < -threshold -> 180 // 倒立
            x < -threshold -> 90  // 左横屏
            else -> currentOrientation // 保持当前方向
        }
    }

    private fun updateCameraOrientation() {
        // 更新ImageCapture的方向
        imageCapture?.targetRotation = when (currentOrientation) {
            0 -> android.view.Surface.ROTATION_0    // 竖屏
            90 -> android.view.Surface.ROTATION_90  // 左横屏
            180 -> android.view.Surface.ROTATION_180 // 倒立
            270 -> android.view.Surface.ROTATION_270 // 右横屏
            else -> android.view.Surface.ROTATION_0
        }

        Log.d("MainActivity", "相机方向已更新: $currentOrientation°")
    }

    private fun getIPAddress(): String {
        val wifiManager = getSystemService(Context.WIFI_SERVICE) as WifiManager
        val wifiInfo = wifiManager.connectionInfo
        val ipAddress = wifiInfo.ipAddress
        return String.format("%d.%d.%d.%d",
            (ipAddress and 0xff),
            (ipAddress shr 8 and 0xff),
            (ipAddress shr 16 and 0xff),
            (ipAddress shr 24 and 0xff)
        )
    }

    private fun startServer() {
        Thread {
            try {
                serverSocket = ServerSocket(8080)
                isServerRunning = true
                Log.d("MainActivity", "Server started on port 8080")

                while (isServerRunning) {
                    try {
                        val socket = serverSocket.accept()
                        val clientAddress = socket.remoteSocketAddress.toString()
                        Log.d("MainActivity", "Client connected: $clientAddress")

                        // 关闭之前的连接
                        clientSocket?.close()
                        clientSocket = socket
                        connectedPcInfo = clientAddress

                        // 更新连接状态
                        updateConnectionStatus("PC已连接: $clientAddress")

                        // 在新线程中处理客户端
                        Thread { handleClient(socket) }.start()

                    } catch (e: IOException) {
                        if (isServerRunning) {
                            Log.e("MainActivity", "Error accepting client: ${e.message}")
                        }
                    }
                }
            } catch (e: IOException) {
                Log.e("MainActivity", "Server error: ${e.message}")
            }
        }.start()
    }

    private fun handleClient(socket: Socket) {
        try {
            val inputStream = socket.getInputStream()
            val outputStream = socket.getOutputStream()
            val buffer = ByteArray(1024)

            // 发送连接确认
            outputStream.write("CONNECTED".toByteArray())
            outputStream.flush()

            Log.d("MainActivity", "Client handler started")

            while (!socket.isClosed && socket.isConnected) {
                try {
                    val bytesRead = inputStream.read(buffer)
                    if (bytesRead == -1) {
                        break // 客户端断开连接
                    }

                    val message = String(buffer, 0, bytesRead).trim()
                    Log.d("MainActivity", "Received command: $message")

                    when (message) {
                        "TAKE_PHOTO" -> {
                            // 立即确认收到命令
                            outputStream.write("COMMAND_RECEIVED".toByteArray())
                            outputStream.flush()

                            // 在主线程中显示提示和执行拍照
                            runOnUiThread {
                                Toast.makeText(this@MainActivity, "收到拍照指令", Toast.LENGTH_SHORT).show()
                                takePhoto()
                            }
                        }
                        "PING" -> {
                            outputStream.write("PONG".toByteArray())
                            outputStream.flush()
                        }
                        "DISCONNECT" -> {
                            Log.d("MainActivity", "Client requested disconnect")
                            break
                        }
                        else -> {
                            Log.w("MainActivity", "Unknown command: $message")
                        }
                    }
                } catch (e: IOException) {
                    Log.e("MainActivity", "Error reading from client: ${e.message}")
                    break
                }
            }
        } catch (e: IOException) {
            Log.e("MainActivity", "Client handler error: ${e.message}")
        } finally {
            try {
                if (socket == clientSocket) {
                    clientSocket = null
                    connectedPcInfo = null
                    // 更新连接状态
                    updateConnectionStatus("等待PC连接...")
                }
                socket.close()
                Log.d("MainActivity", "Client disconnected")
            } catch (e: IOException) {
                Log.e("MainActivity", "Error closing client socket: ${e.message}")
            }
        }
    }
}