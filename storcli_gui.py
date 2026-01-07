import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import subprocess
import threading
import os
import sys
from datetime import datetime

# Enable DPI awareness for Windows
try:
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(1)
except:
    pass

class StorCLIGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("StorCLI Manager")
        
        # Force window to appear on top initially
        self.root.lift()
        self.root.attributes('-topmost', True)
        self.root.after_idle(self.root.attributes, '-topmost', False)
        self.root.geometry("1280x1060")
        
        # Chemin vers storcli.exe (à modifier selon votre installation)
        self.storcli_path = "storcli64.exe"  # ou "C:\\Program Files\\...\\storcli.exe"
        
        # Frame principal
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # StorCLI path configuration
        path_frame = ttk.LabelFrame(main_frame, text="Configuration", padding="5")
        path_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(path_frame, text="StorCLI Path:").grid(row=0, column=0, sticky=tk.W)
        self.path_entry = ttk.Entry(path_frame, width=50)
        self.path_entry.insert(0, self.storcli_path)
        self.path_entry.grid(row=0, column=1, padx=5, sticky=(tk.W, tk.E))
        
        ttk.Button(path_frame, text="Test", command=self.test_storcli).grid(row=0, column=2, padx=5)
        
        # Command buttons frame
        cmd_frame = ttk.LabelFrame(main_frame, text="Quick Commands", padding="10")
        cmd_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5, padx=(0, 5))
        
        # Command buttons
        commands = [
            ("Controller Info /c0", "/c0 show", False),
            ("RAID Status /c0", "/c0/vAll show", False),
            ("Virtual Drives Detailed", "/c0/vAll show all", False),
            ("Rebuild In Progress", "/c0/eAll/sAll show rebuild", False),
        ]
        
        row_idx = 0
        for label, cmd, is_dangerous in commands:
            btn = ttk.Button(cmd_frame, text=label, 
                           command=lambda c=cmd: self.run_command(c))
            btn.grid(row=row_idx, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=2)
            row_idx += 1
        
        # Show All Drives and Physical Drives Info on same row
        ttk.Button(cmd_frame, text="Show All Drives",
                  command=lambda: self.run_command("/cAll/eAll/sAll show")).grid(row=row_idx, column=0, columnspan=1, sticky=(tk.W, tk.E), pady=2, padx=(0, 2))
        ttk.Button(cmd_frame, text="Physical Drives Info /c0",
                  command=lambda: self.run_command("/c0/eAll/sAll show all")).grid(row=row_idx, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=2, padx=(2, 0))
        row_idx += 1
        
        # Event Logs row with two buttons (View and Export)
        ttk.Button(cmd_frame, text="View Event Logs",
                  command=lambda: self.run_command("/c0 show events")).grid(row=row_idx, column=0, columnspan=1, sticky=(tk.W, tk.E), pady=2, padx=(0, 2))
        ttk.Button(cmd_frame, text="Export Event Logs",
                  command=self.export_event_logs).grid(row=row_idx, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=2, padx=(2, 0))
        row_idx += 1
        
        # CLEAR RAID Config button at the bottom
        btn = ttk.Button(cmd_frame, text="⚠️ CLEAR RAID Config /c0",
                        command=lambda: self.confirm_dangerous_command("/c0/fall delete", "⚠️ CLEAR RAID Config /c0"))
        btn.configure(style='Danger.TButton')
        btn.grid(row=row_idx, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=2)
        row_idx += 1
        
        # Séparateur
        ttk.Separator(cmd_frame, orient='horizontal').grid(row=row_idx, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        row_idx += 1
        
        # Patrol Read
        ttk.Label(cmd_frame, text="Patrol Read:", font=('TkDefaultFont', 9, 'bold')).grid(row=row_idx, column=0, sticky=tk.W, pady=2)
        ttk.Button(cmd_frame, text="Status", width=12,
                  command=lambda: self.run_command("/c0 show pr")).grid(row=row_idx, column=1, padx=2, pady=2)
        ttk.Button(cmd_frame, text="ON", width=12,
                  command=self.start_patrol_read).grid(row=row_idx, column=2, padx=2, pady=2)
        ttk.Button(cmd_frame, text="OFF", width=12,
                  command=lambda: self.run_command("/c0 stop pr")).grid(row=row_idx, column=3, padx=2, pady=2)
        row_idx += 1
        
        # Consistency Check
        ttk.Label(cmd_frame, text="Consistency Check:", font=('TkDefaultFont', 9, 'bold')).grid(row=row_idx, column=0, sticky=tk.W, pady=2)
        ttk.Button(cmd_frame, text="Status", width=12,
                  command=lambda: self.run_command("/c0 show cc")).grid(row=row_idx, column=1, padx=2, pady=2)
        ttk.Button(cmd_frame, text="ON", width=12,
                  command=lambda: self.run_command("/c0/vAll start cc")).grid(row=row_idx, column=2, padx=2, pady=2)
        ttk.Button(cmd_frame, text="OFF", width=12,
                  command=lambda: self.run_command("/c0/vAll stop cc")).grid(row=row_idx, column=3, padx=2, pady=2)
        
        # Custom command frame
        custom_frame = ttk.LabelFrame(main_frame, text="Custom Command", padding="10")
        custom_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=5, padx=(0, 5))
        
        ttk.Label(custom_frame, text="Parameters:").grid(row=0, column=0, sticky=tk.W)
        self.custom_entry = ttk.Entry(custom_frame, width=40)
        self.custom_entry.grid(row=0, column=1, padx=5, sticky=(tk.W, tk.E))
        self.custom_entry.bind('<Return>', lambda e: self.run_custom_command())
        
        ttk.Button(custom_frame, text="Execute", 
                  command=self.run_custom_command).grid(row=0, column=2, padx=5)
        
        # Output area
        output_frame = ttk.LabelFrame(main_frame, text="Output", padding="5")
        output_frame.grid(row=1, column=1, rowspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        self.output_text = scrolledtext.ScrolledText(output_frame, width=60, height=30, 
                                                     font=("Consolas", 9))
        self.output_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Clear output button
        ttk.Button(output_frame, text="Clear", 
                  command=self.clear_output).grid(row=1, column=0, pady=5)
        
        # Configuration du redimensionnement
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        cmd_frame.columnconfigure(0, weight=1)
        custom_frame.columnconfigure(1, weight=1)
        output_frame.columnconfigure(0, weight=1)
        output_frame.rowconfigure(0, weight=1)
        
    def test_storcli(self):
        """Test if storcli is accessible"""
        self.storcli_path = self.path_entry.get()
        self.run_command("show")
    
    def confirm_dangerous_command(self, cmd, label):
        """Ask confirmation for dangerous commands"""
        response = messagebox.askyesno(
            "Confirmation Required",
            f"WARNING: This command will DELETE the RAID configuration!\n\n"
            f"Command: {cmd}\n\n"
            f"All virtual drives will be deleted and drives will be reset.\n\n"
            f"Are you ABSOLUTELY sure you want to continue?",
            icon='warning'
        )
        if response:
            self.run_command(cmd)
    
    def start_patrol_read(self):
        """Enable and start patrol read with proper sequence"""
        # Show warning about limitations
        messagebox.showwarning(
            "Patrol Read Limitation",
            "Note: If RAID initialization is ongoing, patrol read cannot be used.\n\n"
            "The system will now:\n"
            "1. Enable manual patrol read mode\n"
            "2. Start patrol read"
        )
        
        # Execute commands in a thread
        thread = threading.Thread(target=self._start_patrol_read_thread)
        thread.daemon = True
        thread.start()
    
    def _start_patrol_read_thread(self):
        """Execute patrol read commands in sequence"""
        try:
            self.append_output(f"\n{'='*60}\n")
            self.append_output(f"Enabling Patrol Read (2-step process)\n")
            self.append_output(f"{'='*60}\n\n")
            
            # Step 1: Enable manual patrol read mode
            self.append_output("Step 1: Enabling manual patrol read mode...\n")
            cmd1 = f'"{self.storcli_path}" /c0 set patrolread=on mode=manual'
            result1 = subprocess.run(
                cmd1,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result1.returncode == 0:
                self.append_output(result1.stdout)
                self.append_output("✓ Manual patrol read mode enabled\n\n")
            else:
                self.append_output(f"ERROR (code {result1.returncode}):\n")
                self.append_output(result1.stderr if result1.stderr else result1.stdout)
                self.append_output("\n⚠ Failed to enable patrol read mode, aborting...\n")
                return
            
            # Step 2: Start patrol read
            self.append_output("Step 2: Starting patrol read...\n")
            cmd2 = f'"{self.storcli_path}" /c0 start pr'
            result2 = subprocess.run(
                cmd2,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result2.returncode == 0:
                self.append_output(result2.stdout)
                self.append_output("\n✓ Patrol read started successfully\n")
            else:
                self.append_output(f"ERROR (code {result2.returncode}):\n")
                self.append_output(result2.stderr if result2.stderr else result2.stdout)
            
            self.append_output(f"\n{'='*60}\n")
            
        except subprocess.TimeoutExpired:
            self.append_output("ERROR: Timeout (>30s)\n")
        except Exception as e:
            self.append_output(f"ERROR: {str(e)}\n")
        
    def run_command(self, params):
        """Execute a storcli command in a separate thread"""
        self.storcli_path = self.path_entry.get()
        thread = threading.Thread(target=self._execute_command, args=(params,))
        thread.daemon = True
        thread.start()
        
    def run_custom_command(self):
        """Execute a custom command"""
        params = self.custom_entry.get().strip()
        if params:
            self.run_command(params)
        
    def _execute_command(self, params):
        """Actually execute the command (in a thread)"""
        try:
            self.append_output(f"\n{'='*60}\n")
            self.append_output(f"Command: {self.storcli_path} {params}\n")
            self.append_output(f"{'='*60}\n\n")
            
            cmd = f'"{self.storcli_path}" {params}'
            
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                self.append_output(result.stdout)
            else:
                self.append_output(f"ERROR (code {result.returncode}):\n")
                self.append_output(result.stderr if result.stderr else result.stdout)
                
        except subprocess.TimeoutExpired:
            self.append_output("ERROR: Timeout (>30s)\n")
        except FileNotFoundError:
            self.append_output(f"ERROR: storcli not found at: {self.storcli_path}\n")
            self.append_output("Check the path in configuration.\n")
        except Exception as e:
            self.append_output(f"ERROR: {str(e)}\n")
    
    def append_output(self, text):
        """Add text to output area (thread-safe)"""
        self.output_text.insert(tk.END, text)
        self.output_text.see(tk.END)
        
    def clear_output(self):
        """Clear the output area"""
        self.output_text.delete(1.0, tk.END)
    
    def export_event_logs(self):
        """Export event logs to a text file"""
        # Ask user where to save the file
        default_filename = f"storcli_events_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        filepath = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=default_filename,
            title="Export Event Logs"
        )
        
        if not filepath:
            return  # User cancelled
        
        # Execute the command in a thread
        thread = threading.Thread(target=self._export_event_logs_thread, args=(filepath,))
        thread.daemon = True
        thread.start()
    
    def _export_event_logs_thread(self, filepath):
        """Execute event log export in a thread"""
        try:
            self.append_output(f"\n{'='*60}\n")
            self.append_output(f"Exporting event logs to: {filepath}\n")
            self.append_output(f"{'='*60}\n\n")
            
            cmd = f'"{self.storcli_path}" /c0 show events'
            
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                # Write to file
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(f"StorCLI Event Logs Export\n")
                    f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"{'='*60}\n\n")
                    f.write(result.stdout)
                
                self.append_output(f"✓ Event logs successfully exported to:\n")
                self.append_output(f"   {filepath}\n")
                messagebox.showinfo("Export Successful", f"Event logs exported to:\n{filepath}")
            else:
                self.append_output(f"ERROR (code {result.returncode}):\n")
                self.append_output(result.stderr if result.stderr else result.stdout)
                messagebox.showerror("Export Failed", "Failed to retrieve event logs")
            
        except subprocess.TimeoutExpired:
            self.append_output("ERROR: Timeout (>30s)\n")
            messagebox.showerror("Export Failed", "Command timeout")
        except Exception as e:
            self.append_output(f"ERROR: {str(e)}\n")
            messagebox.showerror("Export Failed", f"Error: {str(e)}")

def main():
    try:
        root = tk.Tk()
        app = StorCLIGUI(root)
        print("StorCLI GUI started successfully")
        root.mainloop()
    except Exception as e:
        print(f"ERROR: Failed to start GUI: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()
