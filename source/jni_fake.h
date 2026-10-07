/* jni_fake.h -- fake JNI environment for Godot 4.6's android glue.
 * MIT license; see LICENSE. */

#ifndef __JNI_FAKE_H__
#define __JNI_FAKE_H__

extern void *fake_vm;  // JavaVM *
extern void *fake_env; // JNIEnv *

// set when the game calls Godot.forceQuit(); main.c polls it
extern volatile int jni_quit_requested;

void jni_init(void);

// class object handed to the GodotLib native entry points
void *jni_activity_class(void);
void *jni_activity_object(void);

// the java-side singletons GodotLib.initialize() receives
void *jni_godot_object(void);
void *jni_godot_io_object(void);
void *jni_netutils_object(void);
void *jni_dirhandler_object(void);
void *jni_filehandler_object(void);
void *jni_tts_object(void);
void *jni_assetmgr_object(void);
void *jni_surface_object(void);

void *jni_new_string(const char *s);
void *jni_new_string_array(int n, const char **items);
void *jni_new_float_array(int n, const float *data);
void jni_release_local(void *ref);

// PCK read counters: used to decide whether the remaining boot cost is SD I/O
// or GPU/engine work before attempting a large in-memory pack cache.
void jni_log_pck_metrics(const char *phase);

// Optionally copy the PCK into RAM before Godot starts. Returns nonzero only
// when the complete pack is available from memory.
int jni_preload_pck(const char *path);

#endif
