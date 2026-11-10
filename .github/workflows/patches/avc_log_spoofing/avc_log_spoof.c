/* SPDX-License-Identifier: GPL-2.0-only */
/*
 * Expose SUSFS AVC-log spoofing through the KernelSU feature ABI used by
 * SukiSU-Ultra v4.3.0-r2 (feature id 10003). The SukiSU builtin branch keeps
 * SUSFS inline, so the SUSFS implementation is the single source of truth.
 */
#include <linux/jump_label.h>
#include <linux/types.h>

#include "avc_log_spoof.h"
#include "policy/feature.h"
#include "include/klog.h"

#ifdef CONFIG_KSU_SUSFS
extern struct static_key_false susfs_is_avc_log_spoofing_enabled;

static int avc_log_spoof_feature_get(u64 *value)
{
    *value = static_key_enabled(&susfs_is_avc_log_spoofing_enabled) ? 1 : 0;
    return 0;
}

static int avc_log_spoof_feature_set(u64 value)
{
    bool enable = value != 0;

    if (enable)
        static_branch_enable(&susfs_is_avc_log_spoofing_enabled);
    else
        static_branch_disable(&susfs_is_avc_log_spoofing_enabled);

    pr_info("avc_log_spoof: set to %d\n", enable);
    return 0;
}

static const struct ksu_feature_handler avc_log_spoof_handler = {
    .feature_id = KSU_FEATURE_AVC_SPOOF,
    .name = "avc_spoof",
    .get_handler = avc_log_spoof_feature_get,
    .set_handler = avc_log_spoof_feature_set,
};

void ksu_avc_log_spoof_init(void)
{
    /*
     * The r2 manager treats this feature as enabled by default. Enable the
     * SUSFS jump label before userspace can query or toggle the feature.
     */
    static_branch_enable(&susfs_is_avc_log_spoofing_enabled);

    if (ksu_register_feature_handler(&avc_log_spoof_handler))
        pr_err("avc_log_spoof: failed to register feature handler\n");
    else
        pr_info("avc_log_spoof: enabled by default\n");
}
#else
void ksu_avc_log_spoof_init(void)
{
    pr_warn("avc_log_spoof: disabled because CONFIG_KSU_SUSFS is not set\n");
}
#endif
