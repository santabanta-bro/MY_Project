#include <windows.h>
#include <gdiplus.h>
#include <mmsystem.h>
#include <stdio.h>
#include <stdlib.h>

#pragma comment (lib,"Gdiplus.lib")
#pragma comment(lib, "winmm.lib")

#define NUMPTS 44100*5 // 5 seconds of 44100 Hz mono 16-bit audio
short int waveIn[NUMPTS]; // 'short int' is a 16-bit type; buffer for 5 seconds of audio

// Function to initialize GDI+
void InitializeGDIPlus() {
    Gdiplus::GdiplusStartupInput gdiplusStartupInput;
    ULONG_PTR gdiplusToken;
    Gdiplus::GdiplusStartup(&gdiplusToken, &gdiplusStartupInput, NULL);
}

// Function to get encoder CLSID
int GetEncoderClsid(const WCHAR* format, CLSID* pClsid) {
    UINT num = 0;
    UINT size = 0;
    Gdiplus::GetImageEncodersSize(&num, &size);
    if (size == 0) return -1;

    Gdiplus::ImageCodecInfo* pImageCodecInfo = (Gdiplus::ImageCodecInfo*)(malloc(size));
    if (pImageCodecInfo == NULL) return -1;

    Gdiplus::GetImageEncoders(num, size, pImageCodecInfo);
    for (UINT j = 0; j < num; ++j) {
        if (wcscmp(pImageCodecInfo[j].MimeType, format) == 0) {
            *pClsid = pImageCodecInfo[j].Clsid;
            free(pImageCodecInfo);
            return j;
        }
    }
    free(pImageCodecInfo);
    return -1;
}

// Function to capture a screenshot
void CaptureScreen(const wchar_t* filename) {
    HDC hdcScreen = GetDC(NULL);
    HDC hdcMemDC = CreateCompatibleDC(hdcScreen);

    RECT rc;
    GetClientRect(GetDesktopWindow(), &rc);

    HBITMAP hbmScreen = CreateCompatibleBitmap(hdcScreen, rc.right, rc.bottom);
    SelectObject(hdcMemDC, hbmScreen);

    BitBlt(hdcMemDC, 0, 0, rc.right, rc.bottom, hdcScreen, 0, 0, SRCCOPY);

    Gdiplus::Bitmap bitmap(hbmScreen, (HPALETTE)NULL);
    CLSID clsid;
    if (GetEncoderClsid(L"image/png", &clsid) >= 0) {
        bitmap.Save(filename, &clsid, NULL);
    }

    DeleteObject(hbmScreen);
    DeleteDC(hdcMemDC);
    ReleaseDC(NULL, hdcScreen);
}

// Function to initialize wave format for audio recording
void InitializeWaveFormat(WAVEFORMATEX *pFormat) {
    pFormat->wFormatTag = WAVE_FORMAT_PCM;
    pFormat->nChannels = 1;
    pFormat->nSamplesPerSec = 44100;
    pFormat->nAvgBytesPerSec = 44100 * 2;
    pFormat->nBlockAlign = 2;
    pFormat->wBitsPerSample = 16;
    pFormat->cbSize = 0;
}

// Function to record audio
void RecordAudio() {
    HWAVEIN hWaveIn;
    WAVEFORMATEX pFormat;
    InitializeWaveFormat(&pFormat);

    waveInOpen(&hWaveIn, WAVE_MAPPER, &pFormat, 0L, 0L, WAVE_FORMAT_DIRECT);

    WAVEHDR WaveInHdr;
    WaveInHdr.lpData = (LPSTR)waveIn;
    WaveInHdr.dwBufferLength = NUMPTS * 2;
    WaveInHdr.dwBytesRecorded = 0;
    WaveInHdr.dwUser = 0L;
    WaveInHdr.dwFlags = 0L;
    WaveInHdr.dwLoops = 0L;
    waveInPrepareHeader(hWaveIn, &WaveInHdr, sizeof(WAVEHDR));

    waveInAddBuffer(hWaveIn, &WaveInHdr, sizeof(WAVEHDR));
    waveInStart(hWaveIn);

    Sleep(5000); // Record for 5 seconds

    waveInStop(hWaveIn);
    waveInUnprepareHeader(hWaveIn, &WaveInHdr, sizeof(WAVEHDR));
    waveInClose(hWaveIn);
}

// Function to save audio to a file
void SaveAudio(const char* filename) {
    FILE* file = fopen(filename, "wb");
    fwrite(waveIn, sizeof(short int), NUMPTS, file);
    fclose(file);
}

int main() {
    // Initialize GDI+ for screenshot
    InitializeGDIPlus();

    // Capture screenshot
    CaptureScreen(L"screenshot.png");

    // Record and save audio
    RecordAudio();
    SaveAudio("audio.raw");

    return 0;
}
