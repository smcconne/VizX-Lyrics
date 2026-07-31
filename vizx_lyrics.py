import os
import sys
import argparse

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from rich.console import Console
from rich.traceback import install
from rich.prompt import Prompt
from rich.panel import Panel
from rich.align import Align
from rich.table import Table

from handler import download_lyrics, get_applemusic_instance, CACHE, CONFIG
from config import Configure, DEFAULT_PROVIDERS
from search import search_and_select
from api.provider_manager import ProviderManager
from utils import logger

install()
console = Console()

LOGO = (
    "[bold bright_cyan]"
    "  ██╗   ██╗██╗███████╗██╗  ██╗   ██╗  ██╗   ██╗██████╗ ██╗ ██████╗███████╗\n"
    "  ██║   ██║██║╚══███╔╝╚██╗██╔╝   ██║  ╚██╗ ██╔╝██╔══██╗██║██╔════╝██╔════╝\n"
    "  ██║   ██║██║  ███╔╝  ╚███╔╝    ██║   ╚████╔╝ ██████╔╝██║██║     ███████╗\n"
    "  ╚██╗ ██╔╝██║ ███╔╝   ██╔██╗    ██║    ╚██╔╝  ██╔══██╗██║██║     ╚════██║\n"
    "   ╚████╔╝ ██║███████╗██╔╝ ██╗   ███████╗██║   ██║  ██║██║╚██████╗███████║\n"
    "    ╚═══╝  ╚═╝╚══════╝╚═╝  ╚═╝   ╚══════╝╚═╝   ╚═╝  ╚═╝╚═╝ ╚═════╝╚══════╝"
    "[/bold bright_cyan]\n\n"
)

def print_banner():
    os.system('cls' if os.name == 'nt' else 'clear')
    console.print()
    console.print(Align.center(LOGO))
    console.print()

def configure_formats_menu(config: Configure):
    while True:
        print_banner()
        settings = config.get_settings()
        
        lrc_status = "[bold green]ENABLED[/bold green]" if settings["save_lrc"] else "[bold red]DISABLED[/bold red]"
        txt_status = "[bold green]ENABLED[/bold green]" if settings["save_txt"] else "[bold red]DISABLED[/bold red]"
        ttml_status = "[bold green]ENABLED[/bold green]" if settings["save_ttml"] else "[bold red]DISABLED[/bold red]"
        precision_status = f"[bold yellow]{settings['sync_precision']} ms digits[/bold yellow]"

        menu_text = (
            f"[1] Toggle LRC (.lrc)     : {lrc_status}\n"
            f"[2] Toggle TXT (.txt)     : {txt_status}\n"
            f"[3] Toggle TTML (.ttml)   : {ttml_status}\n"
            f"[4] Preset: Save ONLY LRC (.lrc)\n"
            f"[5] Preset: Save ONLY TTML (.ttml)\n"
            f"[6] Preset: Save ONLY TXT (.txt)\n"
            f"[7] Preset: Save ALL Formats (LRC + TXT + TTML)\n"
            f"[8] Toggle Sync Precision : {precision_status}\n"
            f"[0] Back to Main Menu"
        )

        console.print(Align.center(Panel(menu_text, title="[bold yellow]⚙️ FORMAT & PRECISION SETTINGS[/bold yellow]", border_style="bright_blue", expand=False)))
        choice = Prompt.ask("\n[bold green]> Select an option[/bold green]", choices=["1", "2", "3", "4", "5", "6", "7", "8", "0"])

        if choice == "1":
            config.set_setting("save_lrc", not settings["save_lrc"])
        elif choice == "2":
            config.set_setting("save_txt", not settings["save_txt"])
        elif choice == "3":
            config.set_setting("save_ttml", not settings["save_ttml"])
        elif choice == "4":
            config.set_setting("save_lrc", True)
            config.set_setting("save_txt", False)
            config.set_setting("save_ttml", False)
            logger.info("Format preset updated: ONLY LRC (.lrc)")
        elif choice == "5":
            config.set_setting("save_lrc", False)
            config.set_setting("save_txt", False)
            config.set_setting("save_ttml", True)
            logger.info("Format preset updated: ONLY TTML (.ttml)")
        elif choice == "6":
            config.set_setting("save_lrc", False)
            config.set_setting("save_txt", True)
            config.set_setting("save_ttml", False)
            logger.info("Format preset updated: ONLY TXT (.txt)")
        elif choice == "7":
            config.set_setting("save_lrc", True)
            config.set_setting("save_txt", True)
            config.set_setting("save_ttml", True)
            logger.info("Format preset updated: ALL FORMATS (LRC + TXT + TTML)")
        elif choice == "8":
            new_prec = 3 if settings["sync_precision"] == 2 else 2
            config.set_setting("sync_precision", new_prec)
        elif choice == "0":
            break

def configure_providers_menu(config: Configure):
    pm = ProviderManager(CACHE, CONFIG)
    while True:
        print_banner()
        settings = config.get_settings()
        preferred = settings["preferred_providers"]
        mode = settings["provider_mode"]
        use_hierarchy = settings["use_sync_hierarchy"]

        mode_str = "[bold green]Fallback (First Hit)[/bold green]" if mode == "fallback" else "[bold magenta]Multi-Provider (Save All)[/bold magenta]"
        hier_str = "[bold green]ENABLED (Syllable -> Word -> Line -> Plain)[/bold green]" if use_hierarchy else "[bold yellow]DISABLED (Strict Priority Order)[/bold yellow]"

        table = Table(title="LYRICS PROVIDERS & PRIORITY ORDER", title_justify="center", border_style="bright_cyan")
        table.add_column("Rank", justify="center", style="bold yellow")
        table.add_column("Key", style="cyan")
        table.add_column("Provider Name", style="white")
        table.add_column("Sync Type", justify="center", style="bold green")
        table.add_column("Status", justify="center")

        # First display active providers in preferred priority order
        for idx, key in enumerate(preferred, 1):
            prov = pm.get_provider(key)
            name = prov.name if prov else key
            stype = prov.sync_type if prov else "unknown"
            table.add_row(str(idx), key, name, stype, "[bold green]ACTIVE[/bold green]")

        # Then display disabled providers at the bottom
        for key in DEFAULT_PROVIDERS:
            if key not in preferred:
                prov = pm.get_provider(key)
                name = prov.name if prov else key
                stype = prov.sync_type if prov else "unknown"
                table.add_row("-", key, name, stype, "[bold red]OFF[/bold red]")

        console.print(Align.center(table))
        console.print()

        options_text = (
            f"Mode: {mode_str}  |  Sync Hierarchy: {hier_str}\n\n"
            f"[1] Toggle Provider Mode (Fallback vs Multi-Save)\n"
            f"[2] Toggle Sync Hierarchy Preference\n"
            f"[3] Enable/Disable Provider Key\n"
            f"[4] Move Provider Priority Up\n"
            f"[5] Move Provider Priority Down\n"
            f"[6] Reset Providers to Default Priority\n"
            f"[7] Set Cubey / Better Lyrics JWT Token\n"
            f"[0] Back to Main Menu"
        )
        console.print(Align.center(Panel(options_text, border_style="bright_yellow", expand=False)))
        choice = Prompt.ask("\n[bold green]> Select an option[/bold green]", choices=["1", "2", "3", "4", "5", "6", "7", "0"])

        if choice == "1":
            new_mode = "multi" if mode == "fallback" else "fallback"
            config.set_setting("provider_mode", new_mode)
        elif choice == "2":
            config.set_setting("use_sync_hierarchy", not use_hierarchy)
        elif choice == "3":
            key_input = Prompt.ask("\n[bold green]> Enter Provider Key to toggle[/bold green]").strip()
            if key_input in DEFAULT_PROVIDERS:
                if key_input in preferred:
                    preferred.remove(key_input)
                else:
                    preferred.append(key_input)
                config.set_setting("preferred_providers", preferred)
            else:
                logger.warning(f"Invalid provider key: {key_input}")
        elif choice == "4":
            key_input = Prompt.ask("\n[bold green]> Enter Provider Key to move UP[/bold green]").strip()
            if key_input in preferred:
                idx = preferred.index(key_input)
                if idx > 0:
                    preferred[idx], preferred[idx-1] = preferred[idx-1], preferred[idx]
                    config.set_setting("preferred_providers", preferred)
        elif choice == "5":
            key_input = Prompt.ask("\n[bold green]> Enter Provider Key to move DOWN[/bold green]").strip()
            if key_input in preferred:
                idx = preferred.index(key_input)
                if idx < len(preferred) - 1:
                    preferred[idx], preferred[idx+1] = preferred[idx+1], preferred[idx]
                    config.set_setting("preferred_providers", preferred)
        elif choice == "6":
            config.set_setting("preferred_providers", list(DEFAULT_PROVIDERS))
            logger.info("Providers reset to default order.")
        elif choice == "7":
            curr_token = settings.get("cubey_jwt_token", None)
            display_tok = f"[bold green]{curr_token[:15]}... ({len(curr_token)} chars)[/bold green]" if curr_token else "[dim]None[/dim]"
            console.print(f"\n[bold yellow]Current Cubey JWT Token:[/bold yellow] {display_tok}")
            token_in = input("\n> Enter JWT Token (type 'clear' to remove, or press Enter to keep current): ").strip().strip("'\"")
            if token_in.lower() == "clear":
                config.set_setting("cubey_jwt_token", None)
                logger.info("Cubey JWT Token cleared!")
            elif token_in:
                config.set_setting("cubey_jwt_token", token_in)
                logger.info("Cubey JWT Token updated successfully!")
        elif choice == "0":
            break

def search_custom_provider_menu(config: Configure):
    print_banner()
    pm = ProviderManager(CACHE, CONFIG)
    settings = config.get_settings()

    table = Table(title="SELECT A CUSTOM PROVIDER FOR SEARCH", title_justify="center", border_style="bright_cyan")
    table.add_column("#", justify="center", style="bold yellow")
    table.add_column("Key", style="cyan")
    table.add_column("Provider Name", style="white")
    table.add_column("Sync Type", justify="center", style="bold green")

    for idx, key in enumerate(DEFAULT_PROVIDERS, 1):
        prov = pm.get_provider(key)
        name = prov.name if prov else key
        stype = prov.sync_type if prov else "unknown"
        table.add_row(str(idx), key, name, stype)

    console.print(Align.center(table))
    console.print()

    choices = [str(i) for i in range(1, len(DEFAULT_PROVIDERS) + 1)] + ["0"]
    choice = Prompt.ask("\n[bold green]> Select a provider number (or 0 to cancel)[/bold green]", choices=choices)

    if choice == "0":
        return

    selected_key = DEFAULT_PROVIDERS[int(choice) - 1]
    selected_prov = pm.get_provider(selected_key)
    prov_name = selected_prov.name if selected_prov else selected_key

    console.print(f"\n[bold yellow]Selected Provider:[/bold yellow] [bold cyan]{prov_name} ({selected_key})[/bold cyan]\n")

    input_mode = Prompt.ask(
        "[bold green]> Input Type: [1] Search Query  [2] Apple Music URL  [0] Cancel[/bold green]",
        choices=["1", "2", "0"]
    )

    url = None
    if input_mode == "1":
        applemusic = get_applemusic_instance(settings["sync_precision"])
        url = search_and_select(applemusic)
    elif input_mode == "2":
        url_in = Prompt.ask("\n[bold green]> Enter Apple Music Song or Album URL[/bold green]")
        if url_in:
            url = url_in.strip()

    if url:
        logger.info(f"Downloading using custom provider: {prov_name} ({selected_key})...")
        download_lyrics(
            url=url,
            save_lrc=settings["save_lrc"],
            save_txt=settings["save_txt"],
            save_ttml=settings["save_ttml"],
            sync_precision=settings["sync_precision"],
            output_dir=settings["output_dir"],
            preferred_providers=[selected_key],
            provider_mode="fallback",
            use_sync_hierarchy=False
        )

def search_all_providers_menu(config: Configure):
    print_banner()
    settings = config.get_settings()
    applemusic = get_applemusic_instance(settings["sync_precision"])
    url = search_and_select(applemusic)
    if url:
        logger.info("Downloading lyrics from ALL active providers...")
        download_lyrics(
            url=url,
            save_lrc=settings["save_lrc"],
            save_txt=settings["save_txt"],
            save_ttml=settings["save_ttml"],
            sync_precision=settings["sync_precision"],
            output_dir=settings["output_dir"],
            provider_mode="multi",
            use_sync_hierarchy=False
        )

def configure_storage_menu(config: Configure):
    while True:
        print_banner()
        settings = config.get_settings()
        out_dir = settings["output_dir"]
        sub_status = "[bold green]ENABLED (downloads/Track/Provider/file.lrc)[/bold green]" if settings.get("organize_by_provider") else "[bold yellow]DISABLED (downloads/Track/file (key).lrc)[/bold yellow]"

        menu_text = (
            f"[bold yellow]Current Output Directory:[/bold yellow] [bold white]{out_dir}[/bold white]\n"
            f"[bold yellow]Subfolder Organization:[/bold yellow] {sub_status}\n\n"
            f"[1] Change Download Output Folder\n"
            f"[2] Toggle Provider Subfolder Organization (Multi-Provider Mode)\n"
            f"[0] Back to Main Menu"
        )
        console.print(Align.center(Panel(menu_text, title="[bold cyan]📁 DOWNLOAD STORAGE CONFIGURATION[/bold cyan]", border_style="bright_cyan", expand=False)))
        choice = Prompt.ask("\n[bold green]> Select an option[/bold green]", choices=["1", "2", "0"])

        if choice == "1":
            new_dir = input("\n> Enter new output directory (or press Enter to keep current): ").strip()
            if new_dir:
                config.set_setting("output_dir", new_dir)
                logger.info(f"Output directory updated to: {new_dir}")
        elif choice == "2":
            new_val = not settings.get("organize_by_provider", False)
            config.set_setting("organize_by_provider", new_val)
            logger.info(f"Provider subfolder organization updated: {new_val}")
        elif choice == "0":
            break

def main_menu():
    config = Configure(CONFIG)
    
    while True:
        print_banner()
        settings = config.get_settings()
        
        menu_text = (
            "[bold cyan][1][/bold cyan] 🔍 [bold white]Search & Download Lyrics (Priority Pipeline)[/bold white]\n"
            "[bold cyan][2][/bold cyan] 🎯 [bold white]Search & Download via Custom Provider[/bold white]\n"
            "[bold cyan][3][/bold cyan] 🌐 [bold white]Search & Download from ALL Providers (Save All)[/bold white]\n"
            "[bold cyan][4][/bold cyan] 🔗 [bold white]Download via Apple Music URL[/bold white]\n"
            "[bold cyan][5][/bold cyan] ⚙️ [bold white]Configure Lyrics Formats & Precision[/bold white]\n"
            "[bold cyan][6][/bold cyan] 🎛️ [bold white]Configure Lyric Providers & Priority[/bold white]\n"
            "[bold cyan][7][/bold cyan] 📁 [bold white]Configure Download Output Folder[/bold white]\n"
            "[bold cyan][0][/bold cyan] 🚪 [bold red]Exit[/bold red]"
        )

        console.print(Align.center(Panel(menu_text, title="[bold bright_cyan]VIZX-LYRICS MAIN MENU[/bold bright_cyan]", title_align="center", border_style="bright_cyan", expand=False)))
        choice = Prompt.ask("\n[bold green]> Select an option[/bold green]", choices=["1", "2", "3", "4", "5", "6", "7", "0"])

        if choice == "1":
            applemusic = get_applemusic_instance(settings["sync_precision"])
            url = search_and_select(applemusic)
            if url:
                download_lyrics(
                    url=url,
                    save_lrc=settings["save_lrc"],
                    save_txt=settings["save_txt"],
                    save_ttml=settings["save_ttml"],
                    sync_precision=settings["sync_precision"],
                    output_dir=settings["output_dir"]
                )
                Prompt.ask("\n[dim]Press Enter to return to main menu...[/dim]")
        elif choice == "2":
            search_custom_provider_menu(config)
            Prompt.ask("\n[dim]Press Enter to return to main menu...[/dim]")
        elif choice == "3":
            search_all_providers_menu(config)
            Prompt.ask("\n[dim]Press Enter to return to main menu...[/dim]")
        elif choice == "4":
            url = Prompt.ask("\n[bold green]> Enter Apple Music Song or Album URL[/bold green]")
            if url:
                download_lyrics(
                    url=url.strip(),
                    save_lrc=settings["save_lrc"],
                    save_txt=settings["save_txt"],
                    save_ttml=settings["save_ttml"],
                    sync_precision=settings["sync_precision"],
                    output_dir=settings["output_dir"]
                )
                Prompt.ask("\n[dim]Press Enter to return to main menu...[/dim]")
        elif choice == "5":
            configure_formats_menu(config)
        elif choice == "6":
            configure_providers_menu(config)
        elif choice == "7":
            configure_storage_menu(config)
            Prompt.ask("\n[dim]Press Enter to return to main menu...[/dim]")
        elif choice == "0":
            console.print("\n[bold yellow]Thank you for using VizX-Lyrics![/bold yellow]")
            sys.exit(0)

def main():
    parser = argparse.ArgumentParser(
        description="VizX-Lyrics: Multi-Source Lyrics Downloader & Search"
    )
    parser.add_argument(
        '-v',
        '--version',
        action='version',
        version='VizX-Lyrics v2.0.0'
    )
    parser.add_argument(
        '-q',
        '--query',
        help="Search query to search Apple Music catalog",
        type=str
    )
    parser.add_argument(
        '-s',
        '--sync',
        help="Save timecode's in 00:00.000 format (three ms points)",
        action="store_true"
    )
    parser.add_argument(
        '--no-txt',
        help="Don't save lyrics as a .txt file",
        action="store_true"
    )
    parser.add_argument(
        '--no-lrc',
        help="Don't save time-synced lyrics as a .lrc file",
        action="store_true"
    )
    parser.add_argument(
        '--no-ttml',
        help="Don't save raw lyrics as a .ttml file",
        action="store_true"
    )
    parser.add_argument(
        '-o',
        '--output',
        help="Custom output directory path",
        type=str
    )
    parser.add_argument(
        '-p',
        '--providers',
        help="Comma-separated list of active provider keys in priority order",
        type=str
    )
    parser.add_argument(
        '-a',
        '--all-providers',
        action='store_true',
        help="Download lyrics from ALL active providers simultaneously"
    )
    parser.add_argument(
        '--provider-mode',
        choices=['fallback', 'multi'],
        help="Provider selection mode: fallback (first hit) or multi (save all)",
        type=str
    )
    parser.add_argument(
        '--list-providers',
        help="List all available lyric providers and exit",
        action="store_true"
    )
    parser.add_argument(
        'url',
        nargs='?',
        help="Apple Music URL for an album or a song",
        type=str
    )
    
    args = parser.parse_args()

    if args.list_providers:
        pm = ProviderManager(CACHE, CONFIG)
        config = Configure(CONFIG)
        settings = config.get_settings()
        preferred = settings["preferred_providers"]

        table = Table(title="Available Lyric Providers in VizX-Lyrics", border_style="cyan")
        table.add_column("Rank", justify="center", style="bold yellow")
        table.add_column("Key", style="cyan")
        table.add_column("Provider Name", style="white")
        table.add_column("Sync Type", justify="center", style="bold green")

        for idx, key in enumerate(preferred, 1):
            prov = pm.get_provider(key)
            name = prov.name if prov else key
            stype = prov.sync_type if prov else "unknown"
            table.add_row(str(idx), key, name, stype)

        for key in DEFAULT_PROVIDERS:
            if key not in preferred:
                prov = pm.get_provider(key)
                name = prov.name if prov else key
                stype = prov.sync_type if prov else "unknown"
                table.add_row("-", key, name, stype)

        console.print(table)
        return

    provider_mode = "multi" if args.all_providers else args.provider_mode

    # Direct search mode via -q / --query
    if args.query:
        print_banner()
        config = Configure(CONFIG)
        settings = config.get_settings()
        sync_precision = 3 if args.sync else settings["sync_precision"]
        applemusic = get_applemusic_instance(sync_precision)
        url = search_and_select(applemusic, query=args.query)
        if url:
            output_dir = args.output or settings["output_dir"]
            providers = [p.strip() for p in args.providers.split(",")] if args.providers else None
            download_lyrics(
                url=url,
                save_lrc=not args.no_lrc,
                save_txt=not args.no_txt,
                save_ttml=not args.no_ttml,
                sync_precision=sync_precision,
                output_dir=output_dir,
                preferred_providers=providers,
                provider_mode=provider_mode,
                use_sync_hierarchy=not args.all_providers
            )
        return

    # Direct URL mode via positional url
    if args.url:
        print_banner()
        config = Configure(CONFIG)
        settings = config.get_settings()
        sync_precision = 3 if args.sync else settings["sync_precision"]
        output_dir = args.output or settings["output_dir"]
        providers = [p.strip() for p in args.providers.split(",")] if args.providers else None
        download_lyrics(
            url=args.url,
            save_lrc=not args.no_lrc,
            save_txt=not args.no_txt,
            save_ttml=not args.no_ttml,
            sync_precision=sync_precision,
            output_dir=output_dir,
            preferred_providers=providers,
            provider_mode=provider_mode,
            use_sync_hierarchy=not args.all_providers
        )
        return

    # Default to Interactive Main Menu
    main_menu()

if __name__ == "__main__":
    main()
