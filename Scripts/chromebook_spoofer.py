from Scripts import utils
from Scripts.datasets import pci_data

class ChromebookSpoofer:
    """
    Handles Chromebook detection and device spoofing for CPU and iGPU.
    
    Chromebooks require special handling in macOS Hackintosh builds because:
    1. Many use low-power CPUs that need spoofing to appear as supported models
    2. Intel iGPUs may need device-id spoofing for proper macOS recognition
    3. Special BIOS/firmware configurations require specific quirks
    """
    
    def __init__(self):
        self.utils = utils.Utils()
        
    def is_chromebook(self, hardware_report):
        """
        Detect if the hardware is a Chromebook based on:
        1. Motherboard manufacturer (GOOGLE)
        2. System devices with known Chromebook PCI IDs
        
        Args:
            hardware_report: Dictionary containing hardware information
            
        Returns:
            bool: True if Chromebook is detected, False otherwise
        """
        # Check motherboard manufacturer
        motherboard_name = hardware_report.get("Motherboard", {}).get("Name", "")
        if "GOOGLE" in motherboard_name.upper():
            return True
        
        # Check for known Chromebook device IDs
        system_devices = hardware_report.get("System Devices", {})
        for device_name, device_props in system_devices.items():
            device_id = device_props.get("Device ID", "")
            subsystem_id = device_props.get("Subsystem ID", "")
            
            if device_id in pci_data.ChromebookIDs:
                if subsystem_id in pci_data.ChromebookIDs[device_id]:
                    return True
        
        return False
    
    def get_chromebook_info(self, hardware_report):
        """
        Extract Chromebook-specific information for logging/debugging.
        
        Args:
            hardware_report: Dictionary containing hardware information
            
        Returns:
            dict: Chromebook information including model hints
        """
        info = {
            "is_chromebook": self.is_chromebook(hardware_report),
            "motherboard": hardware_report.get("Motherboard", {}).get("Name", "Unknown"),
            "chromebook_devices": []
        }
        
        # Identify specific Chromebook devices
        system_devices = hardware_report.get("System Devices", {})
        for device_name, device_props in system_devices.items():
            device_id = device_props.get("Device ID", "")
            subsystem_id = device_props.get("Subsystem ID", "")
            
            if device_id in pci_data.ChromebookIDs:
                if subsystem_id in pci_data.ChromebookIDs[device_id]:
                    info["chromebook_devices"].append({
                        "name": device_name,
                        "device_id": device_id,
                        "subsystem_id": subsystem_id
                    })
        
        return info
    
    def spoof_igpu_for_chromebook(self, hardware_report, macos_version):
        """
        Spoof Intel iGPU device IDs for Chromebooks.
        
        Many Chromebooks use Intel iGPUs that need device-id spoofing to be recognized
        by macOS. This method provides the appropriate spoofed device IDs.
        
        Args:
            hardware_report: Dictionary containing hardware information
            macos_version: Target macOS version (Darwin version format)
            
        Returns:
            dict: Spoofing information for iGPU including device-id and ig-platform-id
        """
        spoof_config = {}
        
        for gpu_name, gpu_props in hardware_report.get("GPU", {}).items():
            gpu_manufacturer = gpu_props.get("Manufacturer", "")
            device_id = gpu_props.get("Device ID", "")
            gpu_type = gpu_props.get("Device Type", "")
            
            # Only process Intel integrated GPUs
            if "Intel" not in gpu_manufacturer or "Integrated" not in gpu_type:
                continue
            
            device_id_short = device_id[5:] if len(device_id) >= 9 else device_id
            
            # Chromebook-specific iGPU spoofing mappings
            # Based on common Chromebook iGPU configurations
            
            # Haswell iGPUs (4th Gen) - Common in older Chromebooks
            if device_id_short.startswith(("0A06", "0A16", "0A1E", "0A26", "0A2E")):
                spoof_config[gpu_name] = {
                    "original_device_id": device_id,
                    "spoofed_device_id": "12040000",  # HD 4400
                    "AAPL,ig-platform-id": "0600260A",  # Haswell mobile framebuffer
                    "reason": "Chromebook Haswell iGPU spoofing"
                }
            
            # Broadwell iGPUs (5th Gen)
            elif device_id_short.startswith(("1606", "1616", "161E", "1626", "162B")):
                spoof_config[gpu_name] = {
                    "original_device_id": device_id,
                    "spoofed_device_id": "16160000",  # HD 5500
                    "AAPL,ig-platform-id": "06002616",  # Broadwell mobile framebuffer
                    "reason": "Chromebook Broadwell iGPU spoofing"
                }
            
            # Skylake iGPUs (6th Gen) - Very common in Chromebooks
            elif device_id_short.startswith(("1906", "1916", "191E", "1926", "192B")):
                spoof_config[gpu_name] = {
                    "original_device_id": device_id,
                    "spoofed_device_id": "16190000",  # HD 520
                    "AAPL,ig-platform-id": "00001619",  # Skylake mobile framebuffer
                    "reason": "Chromebook Skylake iGPU spoofing"
                }
            
            # Kaby Lake iGPUs (7th Gen)
            elif device_id_short.startswith(("5906", "5916", "591E", "5926", "5927")):
                spoof_config[gpu_name] = {
                    "original_device_id": device_id,
                    "spoofed_device_id": "16590000",  # HD 620
                    "AAPL,ig-platform-id": "00001659",  # Kaby Lake mobile framebuffer
                    "reason": "Chromebook Kaby Lake iGPU spoofing"
                }
            
            # Apollo Lake (Goldmont - Common in budget Chromebooks)
            elif device_id_short.startswith(("5A84", "5A85")):
                spoof_config[gpu_name] = {
                    "original_device_id": device_id,
                    "spoofed_device_id": "5A850000",  # HD 505
                    "AAPL,ig-platform-id": "00005A84",  # Apollo Lake framebuffer
                    "reason": "Chromebook Apollo Lake iGPU spoofing"
                }
            
            # Gemini Lake (Goldmont Plus)
            elif device_id_short.startswith(("3184", "3185")):
                spoof_config[gpu_name] = {
                    "original_device_id": device_id,
                    "spoofed_device_id": "85310000",  # UHD 605
                    "AAPL,ig-platform-id": "00003185",  # Gemini Lake framebuffer
                    "reason": "Chromebook Gemini Lake iGPU spoofing"
                }
            
            # Comet Lake (10th Gen)
            elif device_id_short.startswith(("9B41", "9BA5", "9BA8")):
                spoof_config[gpu_name] = {
                    "original_device_id": device_id,
                    "spoofed_device_id": "A53B0000",  # UHD 620
                    "AAPL,ig-platform-id": "0000A53B",  # Comet Lake mobile framebuffer
                    "reason": "Chromebook Comet Lake iGPU spoofing"
                }
            
            # Ice Lake (10th Gen)
            elif device_id_short.startswith(("8A51", "8A52", "8A5A")):
                spoof_config[gpu_name] = {
                    "original_device_id": device_id,
                    "spoofed_device_id": "5A528A00",  # Iris Plus
                    "AAPL,ig-platform-id": "00528A8A",  # Ice Lake mobile framebuffer
                    "reason": "Chromebook Ice Lake iGPU spoofing"
                }
        
        return spoof_config
    
    def spoof_cpu_for_chromebook(self, hardware_report):
        """
        Spoof CPU information for Chromebooks with unsupported CPUs.
        
        Chromebooks often use Intel Celeron/Pentium processors that need spoofing
        to be recognized as supported Core processors in macOS.
        
        Args:
            hardware_report: Dictionary containing hardware information
            
        Returns:
            dict: CPU spoofing information including cpuid values
        """
        cpu_name = hardware_report.get("CPU", {}).get("Processor Name", "")
        cpu_codename = hardware_report.get("CPU", {}).get("Codename", "")
        
        spoof_info = {
            "needs_spoofing": False,
            "original_cpu": cpu_name,
            "reason": ""
        }
        
        # Check if CPU is Celeron or Pentium (common in Chromebooks)
        if "Celeron" in cpu_name or "Pentium" in cpu_name:
            spoof_info["needs_spoofing"] = True
            spoof_info["reason"] = "Chromebook low-end CPU detected (Celeron/Pentium)"
            
            # Determine appropriate Core CPU to spoof based on generation
            if "Haswell" in cpu_codename:
                spoof_info["spoof_as"] = "Core i5-4300U"
                spoof_info["cpuid_data"] = "C3060300"
            elif "Broadwell" in cpu_codename:
                spoof_info["spoof_as"] = "Core i5-5300U"
                spoof_info["cpuid_data"] = "D4060300"
            elif "Skylake" in cpu_codename:
                spoof_info["spoof_as"] = "Core i5-6300U"
                spoof_info["cpuid_data"] = "E3060300"
            elif "Kaby Lake" in cpu_codename:
                spoof_info["spoof_as"] = "Core i5-7300U"
                spoof_info["cpuid_data"] = "E9060300"
            elif "Apollo Lake" in cpu_codename or "Goldmont" in cpu_codename:
                spoof_info["spoof_as"] = "Core i3-7100U"
                spoof_info["cpuid_data"] = "E9060300"
            elif "Gemini Lake" in cpu_codename:
                spoof_info["spoof_as"] = "Core i3-8100"
                spoof_info["cpuid_data"] = "EA060900"
            elif "Comet Lake" in cpu_codename:
                spoof_info["spoof_as"] = "Core i5-10210U"
                spoof_info["cpuid_data"] = "EC060A00"
            elif "Ice Lake" in cpu_codename:
                spoof_info["spoof_as"] = "Core i5-1035G1"
                spoof_info["cpuid_data"] = "E5060700"
            else:
                # Default fallback for unknown generations
                spoof_info["spoof_as"] = "Core i5 (Generic)"
                spoof_info["cpuid_data"] = "E3060300"
        
        return spoof_info
    
    def generate_chromebook_report(self, hardware_report, macos_version):
        """
        Generate a comprehensive report of Chromebook spoofing requirements.
        
        Args:
            hardware_report: Dictionary containing hardware information
            macos_version: Target macOS version (Darwin version format)
            
        Returns:
            dict: Complete spoofing report with all necessary modifications
        """
        report = {
            "is_chromebook": self.is_chromebook(hardware_report),
            "chromebook_info": self.get_chromebook_info(hardware_report),
            "igpu_spoofing": {},
            "cpu_spoofing": {},
            "recommendations": []
        }
        
        if report["is_chromebook"]:
            # Get iGPU spoofing configuration
            report["igpu_spoofing"] = self.spoof_igpu_for_chromebook(hardware_report, macos_version)
            
            # Get CPU spoofing configuration
            report["cpu_spoofing"] = self.spoof_cpu_for_chromebook(hardware_report)
            
            # Generate recommendations
            report["recommendations"].append(
                "Chromebook detected - ProtectMemoryRegions quirk will be enabled"
            )
            
            if report["igpu_spoofing"]:
                report["recommendations"].append(
                    "iGPU spoofing required for proper graphics acceleration"
                )
            
            if report["cpu_spoofing"].get("needs_spoofing"):
                report["recommendations"].append(
                    f"CPU will be spoofed as {report['cpu_spoofing'].get('spoof_as', 'supported model')}"
                )
            
            report["recommendations"].append(
                "Ensure you have disabled firmware write protection before installation"
            )
            
            report["recommendations"].append(
                "ChromeOS firmware may require additional ACPI patches"
            )
        
        return report
    
    def print_chromebook_detection_info(self, hardware_report, macos_version):
        """
        Print user-friendly information about Chromebook detection and spoofing.
        
        Args:
            hardware_report: Dictionary containing hardware information
            macos_version: Target macOS version (Darwin version format)
        """
        report = self.generate_chromebook_report(hardware_report, macos_version)
        
        if not report["is_chromebook"]:
            return
        
        self.utils.head("Chromebook Detection")
        print("")
        print("✓ Chromebook hardware detected!")
        print("")
        print("Motherboard: {}".format(report["chromebook_info"]["motherboard"]))
        
        if report["chromebook_info"]["chromebook_devices"]:
            print("")
            print("Chromebook-specific devices found:")
            for device in report["chromebook_info"]["chromebook_devices"]:
                print("  - {} (Device ID: {}, Subsystem ID: {})".format(
                    device["name"], device["device_id"], device["subsystem_id"]
                ))
        
        print("")
        print("Spoofing Configuration:")
        print("")
        
        # Display CPU spoofing info
        if report["cpu_spoofing"].get("needs_spoofing"):
            print("CPU Spoofing:")
            print("  Original: {}".format(report["cpu_spoofing"]["original_cpu"]))
            print("  Will spoof as: {}".format(report["cpu_spoofing"]["spoof_as"]))
            print("  Reason: {}".format(report["cpu_spoofing"]["reason"]))
            print("")
        
        # Display iGPU spoofing info
        if report["igpu_spoofing"]:
            print("iGPU Spoofing:")
            for gpu_name, spoof_info in report["igpu_spoofing"].items():
                print("  GPU: {}".format(gpu_name))
                print("    Original Device ID: {}".format(spoof_info["original_device_id"]))
                print("    Spoofed Device ID: {}".format(spoof_info["spoofed_device_id"]))
                print("    Framebuffer ID: {}".format(spoof_info["AAPL,ig-platform-id"]))
                print("    Reason: {}".format(spoof_info["reason"]))
            print("")
        
        # Display recommendations
        if report["recommendations"]:
            print("Recommendations:")
            for idx, recommendation in enumerate(report["recommendations"], 1):
                print("  {}. {}".format(idx, recommendation))
            print("")
        
        self.utils.request_input("Press Enter to continue...")
