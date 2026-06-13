#include <windows.h>
#include <shellapi.h>
#include <stdlib.h>
#include <wchar.h>

typedef int(__cdecl *PyMainFunction)(int, wchar_t **);

static void show_error(const wchar_t *message) {
    MessageBoxW(NULL, message, L"Kantar Servisi", MB_OK | MB_ICONERROR);
}

int WINAPI wWinMain(
    HINSTANCE instance,
    HINSTANCE previous_instance,
    PWSTR command_line,
    int show_command
) {
    wchar_t executable_path[MAX_PATH];
    wchar_t python_dll_path[MAX_PATH];
    wchar_t **original_argv;
    wchar_t **python_argv;
    int original_argc = 0;
    int python_argc;
    int index;
    int result;
    HMODULE python_dll;
    PyMainFunction py_main;

    (void)instance;
    (void)previous_instance;
    (void)command_line;
    (void)show_command;

    if (!GetModuleFileNameW(NULL, executable_path, MAX_PATH)) {
        show_error(L"Uygulama dosya yolu okunamadi.");
        return 1;
    }

    wcscpy_s(python_dll_path, MAX_PATH, executable_path);
    wchar_t *last_separator = wcsrchr(python_dll_path, L'\\');
    if (last_separator == NULL) {
        show_error(L"Uygulama klasoru belirlenemedi.");
        return 1;
    }
    *(last_separator + 1) = L'\0';
    wcscat_s(python_dll_path, MAX_PATH, L"python312.dll");

    python_dll = LoadLibraryW(python_dll_path);
    if (python_dll == NULL) {
        show_error(L"Windows uygulama calisma zamani yuklenemedi. Programi yeniden kurun.");
        return 1;
    }

    py_main = (PyMainFunction)GetProcAddress(python_dll, "Py_Main");
    if (py_main == NULL) {
        show_error(L"Windows uygulama baslaticisi gecersiz. Programi yeniden kurun.");
        FreeLibrary(python_dll);
        return 1;
    }

    original_argv = CommandLineToArgvW(GetCommandLineW(), &original_argc);
    if (original_argv == NULL || original_argc < 1) {
        show_error(L"Komut satiri okunamadi.");
        FreeLibrary(python_dll);
        return 1;
    }

    python_argc = original_argc + 2;
    python_argv = calloc((size_t)python_argc + 1, sizeof(wchar_t *));
    if (python_argv == NULL) {
        show_error(L"Uygulama baslatmak icin yeterli bellek yok.");
        LocalFree(original_argv);
        FreeLibrary(python_dll);
        return 1;
    }

    python_argv[0] = original_argv[0];
    python_argv[1] = L"-m";
    python_argv[2] = L"kantar_servis.windows_bootstrap";
    for (index = 1; index < original_argc; index++) {
        python_argv[index + 2] = original_argv[index];
    }

    result = py_main(python_argc, python_argv);
    free(python_argv);
    LocalFree(original_argv);
    FreeLibrary(python_dll);
    return result;
}
