#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void hide_message(const char *input_image, const char *message, const char *output_image) {
    FILE *infile = fopen(input_image, "rb");
    FILE *outfile = fopen(output_image, "wb");

    if (infile == NULL || outfile == NULL) {
        printf("Error opening file.\n");
        return;
    }

    // Copy image data
    char buffer[1024];
    size_t bytesRead;
    while ((bytesRead = fread(buffer, 1, sizeof(buffer), infile)) > 0) {
        fwrite(buffer, 1, bytesRead, outfile);
    }

    // Append message
    size_t message_len = strlen(message);
    fwrite(message, sizeof(char), message_len, outfile);
    fwrite(&message_len, sizeof(size_t), 1, outfile);

    fclose(infile);
    fclose(outfile);
    printf("Message hidden successfully in %s\n", output_image);
}

void extract_message(const char *input_image) {
    FILE *infile = fopen(input_image, "rb");
    if (infile == NULL) {
        printf("Error opening file: %s\n", input_image);
        return;
    }

    // Seek to end to determine file size
    fseek(infile, 0, SEEK_END);
    long file_size = ftell(infile);
    if (file_size < sizeof(size_t)) {
        printf("The file is too small to contain a hidden message.\n");
        fclose(infile);
        return;
    }

    // Seek to where the message length is stored
    fseek(infile, -(long)sizeof(size_t), SEEK_END);
    size_t message_len;
    fread(&message_len, sizeof(size_t), 1, infile);

    // Validate message length
    if (message_len > (size_t)file_size) {
        printf("Invalid message length.\n");
        fclose(infile);
        return;
    }

    // Allocate memory and extract message
    char *message = (char *)malloc(message_len + 1);
    if (message == NULL) {
        printf("Memory allocation failed.\n");
        fclose(infile);
        return;
    }

    fseek(infile, -(long)(message_len + sizeof(size_t)), SEEK_END);
    fread(message, sizeof(char), message_len, infile);
    message[message_len] = '\0';

    printf("Extracted message: %s\n", message);

    free(message);
    fclose(infile);
}

int main(int argc, char *argv[]) {
    if (argc < 3) {
        printf("Usage:\n");
        printf("  Hide message: %s hide <input_image> <message> <output_image>\n", argv[0]);
        printf("  Extract message: %s extract <image_file>\n", argv[0]);
        return 1;
    }

    if (strcmp(argv[1], "hide") == 0 && argc == 5) {
        hide_message(argv[2], argv[3], argv[4]);
    } else if (strcmp(argv[1], "extract") == 0 && argc == 3) {
        extract_message(argv[2]);
    } else {
        printf("Invalid arguments.\n");
    }

    return 0;
}
