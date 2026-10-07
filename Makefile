# Gizmoduck 1.1.2 Nintendo Switch wrapper.

ifeq ($(strip $(DEVKITPRO)),)
$(error Set DEVKITPRO and run this Makefile from the devkitPro MSYS2 shell.)
endif

TOPDIR ?= $(CURDIR)
include $(DEVKITPRO)/libnx/switch_rules

TARGET := gizmoduck
APP_TITLE := Gizmoduck
APP_AUTHOR := Sova Games; Switch port: sklart
APP_VERSION := 1.1.16
# hbmenu only recognizes the JPEG NRO icon payload (as used by the working
# GTASA Unexplored build); PNG is accepted by elf2nro but silently falls back
# to the generic Switch/exclamation icon in hbmenu.
APP_ICON := $(TOPDIR)/assets/icon.jpg
BUILD := build
SOURCES := source
INCLUDES := source
ARCH := -march=armv8-a+crc+crypto -mtune=cortex-a57 -mtp=soft -fPIE
# Keep a persistent wrapper log for hardware diagnosis, but do not ask Godot
# itself for --verbose: on Switch Mesa that enables synchronous GL debug and
# spends much of boot reporting benign driver warnings.
DEBUG ?= 1
GODOT_VERBOSE ?= 0
PYTHON ?= python3
CFLAGS := -g -Wall -Wextra -O2 -ffunction-sections $(ARCH) $(DEFINES) -D__SWITCH__
CFLAGS += $(INCLUDE)
CFLAGS += -DDEBUG_LOG=$(DEBUG)
CFLAGS += -DGODOT_VERBOSE=$(GODOT_VERBOSE)
CXXFLAGS := $(CFLAGS)
ASFLAGS := -g $(ARCH)
LDFLAGS := -specs=$(DEVKITPRO)/libnx/switch.specs -g $(ARCH) -Wl,--allow-multiple-definition -Wl,-Map,$(notdir $*.map)
LIBS := -lGLESv2 -lEGL -lglapi -ldrm_nouveau -lz -lnx -lm
LIBDIRS := $(PORTLIBS) $(LIBNX)

ifneq ($(BUILD),$(notdir $(CURDIR)))
export OUTPUT := $(CURDIR)/$(TARGET)
export TOPDIR := $(CURDIR)
export VPATH := $(foreach dir,$(SOURCES),$(CURDIR)/$(dir))
export DEPSDIR := $(CURDIR)/$(BUILD)
CFILES := $(foreach dir,$(SOURCES),$(notdir $(wildcard $(dir)/*.c)))
CPPFILES := $(foreach dir,$(SOURCES),$(notdir $(wildcard $(dir)/*.cpp)))
SFILES := $(foreach dir,$(SOURCES),$(notdir $(wildcard $(dir)/*.s)))
export OFILES_SRC := $(CPPFILES:.cpp=.o) $(CFILES:.c=.o) $(SFILES:.s=.o)
export OFILES := $(OFILES_SRC)
export INCLUDE := $(foreach dir,$(INCLUDES),-I$(CURDIR)/$(dir)) $(foreach dir,$(LIBDIRS),-I$(dir)/include) -I$(CURDIR)/$(BUILD)
export LIBPATHS := $(foreach dir,$(LIBDIRS),-L$(dir)/lib)
export LD := $(CXX)
# switch_rules creates the .nacp but does not attach it automatically. Pass
# both assets to elf2nro explicitly, otherwise Homebrew Menu shows the generic
# icon and "Unknown author" even though gizmoduck.nacp exists beside the NRO.
export NROFLAGS := --nacp=$(OUTPUT).nacp --icon=$(APP_ICON)
.PHONY: all clean test $(BUILD)
all: $(BUILD)
$(BUILD):
	@[ -d $@ ] || mkdir -p $@
	@$(MAKE) --no-print-directory -C $(BUILD) -f $(CURDIR)/Makefile
clean:
	@rm -fr $(BUILD) $(TARGET).nro $(TARGET).nacp $(TARGET).elf
test:
	@$(PYTHON) -m unittest tests/test_prepare_game.py tests/test_package_sd.py tests/test_verify_sd_layout.py
else
DEPENDS := $(OFILES:.o=.d)
.PHONY: all
all: $(OUTPUT).nro
$(OUTPUT).nro: $(OUTPUT).elf $(OUTPUT).nacp $(APP_ICON)
$(OUTPUT).elf: $(OFILES)
-include $(DEPENDS)
endif
