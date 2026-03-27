from modules.script_callbacks import on_ui_settings
from modules.shared import opts, OptionInfo
from modules import scripts

from gradio import Accordion, Button, Checkbox

try:
    from backend.memory_management import soft_empty_cache, unload_all_models
    _has_unload_all = True
except ImportError:
    _has_unload_all = False
    try:
        from ldm_patched.modules.model_management import soft_empty_cache
        try:
            from ldm_patched.modules.model_management import unload_all_models
            _has_unload_all = True
        except ImportError:
            pass
    except ImportError:

        import torch
        import gc

        def soft_empty_cache():
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()
            gc.collect()


class MemRel(scripts.Script):

    def title(self):
        return "Memory Release"

    def show(self, is_img2img):
        return scripts.AlwaysVisible

    def ui(self, is_img2img):
        with Accordion(label="Memory Release", open=False):
            release_button = Button(
                value="🧹",
                tooltip="Garbage Collect",
                elem_id=self.elem_id("memre_btn"),
            )
            release_button.click(fn=MemRel.mem_release, queue=False)

            if _has_unload_all:
                unload_button = Button(
                    value="🗑️ Unload All Models",
                    tooltip="Unload all models from VRAM",
                    elem_id=self.elem_id("memre_unload_btn"),
                )
                unload_button.click(fn=MemRel.mem_unload_all, queue=False)

    def postprocess_batch(self, *args, **kwargs):
        MemRel.mem_release()
        if getattr(opts, "memre_unload_after_gen", False):
            MemRel.mem_unload_all()

    def postprocess(self, *args, **kwargs):
        MemRel.mem_release()
        if getattr(opts, "memre_unload_after_gen", False):
            MemRel.mem_unload_all()

    @staticmethod
    def mem_release():
        try:
            soft_empty_cache()
        except Exception as e:
            if getattr(opts, "memre_debug", False):
                from modules.errors import display
                display(e, "Memory Release")
        else:
            if getattr(opts, "memre_debug", False):
                print("\nMemory Released!\n")

    @staticmethod
    def mem_unload_all():
        if not _has_unload_all:
            if getattr(opts, "memre_debug", False):
                print("\n[Memory Release] unload_all_models not available in this backend.\n")
            return
        try:
            unload_all_models()
            soft_empty_cache()
        except Exception as e:
            if getattr(opts, "memre_debug", False):
                from modules.errors import display
                display(e, "Memory Release - Unload All Models")
        else:
            if getattr(opts, "memre_debug", False):
                print("\nAll Models Unloaded!\n")


def on_mem_settings():
    opts.add_option(
        "memre_debug",
        OptionInfo(
            False,
            "Memory Release - Debug",
            section=("system", "System"),
            category_id="system",
        ),
    )

    if _has_unload_all:
        opts.add_option(
            "memre_unload_after_gen",
            OptionInfo(
                False,
                "Memory Release - Unload all models after each generation",
                section=("system", "System"),
                category_id="system",
            ),
        )


on_ui_settings(on_mem_settings)
