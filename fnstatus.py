#!/usr/bin/env python3
"""
Enhanced Epic Games Status & Deals Checker (Fixed Version)
Monitors Epic Games services status and displays current free games/promotions
"""

import requests
import time
import sys
import json
from datetime import datetime, timezone
from colorama import init, Fore, Style, Back
from typing import Dict, List, Optional, Any

init(autoreset=True)

# Working API Endpoints (removed the 404 ones)
EPIC_STATUS_URL = "https://status.epicgames.com/api/v2/summary.json"
EPIC_STATUS_CURRENT = "https://status.epicgames.com/api/v2/status.json"
EPIC_INCIDENTS_URL = "https://status.epicgames.com/api/v2/incidents.json"
EPIC_COMPONENTS_URL = "https://status.epicgames.com/api/v2/components.json"
EPIC_FREE_GAMES_URL = "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions"

# Removed these endpoints as they return 404:
# EPIC_INCIDENTS_HISTORY = "https://status.epicgames.com/api/v2/incidents/history.json"
# EPIC_SERVICES_URL = "https://status.epicgames.com/api/v2/services.json"
# EPIC_MAINTENANCE_URL = "https://status.epicgames.com/api/v2/scheduled_maintenances.json"
# EPIC_NEWS_URL = "https://status.epicgames.com/api/v2/news.json"
# EPIC_INCIDENT_TYPES = "https://status.epicgames.com/api/v2/incident_types.json"

HEADERS = {
    "User-Agent": "EpicGamesStatusChecker/Pro 3.0 (Enhanced Status Monitor)",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9"
}

STATUS_MAP = {
    "operational": (f"{Fore.GREEN}OPERATIONAL{Style.RESET_ALL}", "Everything is working normally"),
    "degraded_performance": (f"{Fore.YELLOW}DEGRADED PERFORMANCE{Style.RESET_ALL}", "Some services are slower than usual"),
    "partial_outage": (f"{Fore.RED}*** WARNING: PARTIAL OUTAGE ***{Style.RESET_ALL}", "Some parts may not be working"),
    "major_outage": (f"{Fore.RED}*** CRITICAL: MAJOR OUTAGE ***{Style.RESET_ALL}", "Service is down for most users"),
    "under_maintenance": (f"{Fore.CYAN}MAINTENANCE{Style.RESET_ALL}", "Scheduled maintenance in progress"),
    "unknown": (f"{Fore.MAGENTA}UNKNOWN STATUS{Style.RESET_ALL}", "Status cannot be determined")
}

class EpicGamesMonitor:
    def __init__(self):
        self.last_status_check = None
        self.last_free_games_check = None
        self.last_eac_status = None
        
    def timestamp(self) -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def make_request(self, url: str, timeout: int = 15) -> Optional[Dict]:
        """Make HTTP request with error handling"""
        try:
            response = requests.get(url, headers=HEADERS, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            print(f"{Fore.RED}Timeout fetching: {url}{Style.RESET_ALL}")
            return None
        except requests.exceptions.ConnectionError:
            print(f"{Fore.RED}Connection error for: {url}{Style.RESET_ALL}")
            return None
        except requests.exceptions.HTTPError as e:
            print(f"{Fore.RED}HTTP Error {e.response.status_code}: {url}{Style.RESET_ALL}")
            return None
        except json.JSONDecodeError:
            print(f"{Fore.RED}Invalid JSON response from: {url}{Style.RESET_ALL}")
            return None
        except Exception as e:
            print(f"{Fore.RED}Unexpected error: {e}{Style.RESET_ALL}")
            return None

    def print_banner(self):
        """Display enhanced banner"""
        print(f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════════════╗
║                    EPIC GAMES MONITOR v3.1                        ║
║     Status • Incidents • EAC • Free Games • More! (FIXED)         ║
╚══════════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
""")

    def get_component_by_keywords(self, components: List[Dict], keywords: List[str]) -> Optional[Dict]:
        """Find component by matching keywords in name"""
        for comp in components:
            name = comp.get("name", "").strip().lower()
            if any(keyword.lower() in name for keyword in keywords):
                return comp
        return None

    def print_service_status(self, label: str, component: Optional[Dict]):
        """Print formatted service status"""
        if not component:
            print(f"{Fore.WHITE}{label:<25}{Style.RESET_ALL}: {Fore.MAGENTA}NOT FOUND{Style.RESET_ALL}")
            return
            
        status = component.get("status", "unknown").lower()
        status_display, description = STATUS_MAP.get(status, STATUS_MAP["unknown"])
        
        # Add extra emphasis for outages
        if "outage" in status.lower():
            print(f"{Back.RED}{Fore.WHITE} {label} {Style.RESET_ALL}: {status_display}")
        else:
            print(f"{Fore.WHITE}{label:<25}{Style.RESET_ALL}: {status_display}")

    def display_system_status(self):
        """Display comprehensive system status"""
        print(f"\n{Back.BLUE}{Fore.WHITE} SYSTEM STATUS {Style.RESET_ALL}")
        print("─" * 70)
        
        # Get main status
        status_data = self.make_request(EPIC_STATUS_URL)
        if not status_data:
            print(f"{Fore.RED}Unable to fetch system status{Style.RESET_ALL}")
            return

        components = status_data.get("components", [])
        overall_status = status_data.get("page", {}).get("indicator", "none")
        
        # Overall status with warnings
        if overall_status == "none":
            overall_text = f"{Fore.GREEN}ALL SYSTEMS OPERATIONAL{Style.RESET_ALL}"
        else:
            overall_text = f"{Fore.RED}*** WARNING: ISSUES DETECTED ***{Style.RESET_ALL}"
        
        print(f"{Fore.WHITE}Overall Status{Style.RESET_ALL}: {overall_text}")
        print()

        # Key services
        services = [
            ("Fortnite", ["fortnite"]),
            ("Epic Games Store", ["store", "epic games store"]),
            ("Login/Authentication", ["login", "account", "authentication", "auth"]),
            ("Matchmaking", ["matchmaking", "game services", "lobby"]),
            ("Friends & Social", ["friends", "social"]),
            ("Cloud Save", ["cloud save", "save"]),
            ("Downloads", ["download", "launcher"]),
            ("Payment Processing", ["payment", "purchase"]),
            ("Support System", ["support", "help"]),
            ("Rocket League", ["rocket league"]),
            ("Fall Guys", ["fall guys"])
        ]

        for service_name, keywords in services:
            component = self.get_component_by_keywords(components, keywords)
            self.print_service_status(service_name, component)

    def display_components_detailed(self):
        """Display all available components for detailed status"""
        print(f"\n{Back.GREEN}{Fore.WHITE} DETAILED COMPONENTS STATUS {Style.RESET_ALL}")
        print("─" * 70)
        
        components_data = self.make_request(EPIC_COMPONENTS_URL)
        if not components_data:
            print(f"{Fore.RED}Unable to fetch components data{Style.RESET_ALL}")
            return

        components = components_data.get("components", [])
        if not components:
            print(f"{Fore.YELLOW}No components data available{Style.RESET_ALL}")
            return

        # Group components by status
        operational = []
        issues = []
        
        for component in components:
            name = component.get("name", "Unknown Component")
            status = component.get("status", "unknown").lower()
            
            if status == "operational":
                operational.append(name)
            else:
                issues.append((name, status))

        # Show issues first
        if issues:
            print(f"{Fore.RED}COMPONENTS WITH ISSUES:{Style.RESET_ALL}")
            for name, status in issues:
                status_display, _ = STATUS_MAP.get(status, STATUS_MAP["unknown"])
                print(f"  {Fore.WHITE}{name:<35}{Style.RESET_ALL}: {status_display}")
            print()

        # Show operational count
        if operational:
            print(f"{Fore.GREEN}{len(operational)} components operational{Style.RESET_ALL}")
            # Optionally show first few operational components
            if len(operational) <= 5:
                for name in operational:
                    print(f"  {Fore.WHITE}{name:<35}{Style.RESET_ALL}: {Fore.GREEN}OPERATIONAL{Style.RESET_ALL}")
            else:
                print(f"  Including: {', '.join(operational[:3])}, and {len(operational)-3} more...")

    def display_easy_anticheat_status(self):
        """Display Easy Anti-Cheat specific monitoring"""
        print(f"\n{Back.MAGENTA}{Fore.WHITE} EASY ANTI-CHEAT (EAC) STATUS {Style.RESET_ALL}")
        print("─" * 70)
        
        # Check components for EAC
        status_data = self.make_request(EPIC_STATUS_URL)
        if status_data:
            components = status_data.get("components", [])
            eac_keywords = ["anti", "cheat", "eac", "easy anti", "anticheat"]
            eac_component = self.get_component_by_keywords(components, eac_keywords)
            
            if eac_component:
                self.print_service_status("Easy Anti-Cheat", eac_component)
                current_status = eac_component.get("status", "unknown")
                
                # Check for status changes
                if self.last_eac_status and self.last_eac_status != current_status:
                    print(f"{Back.YELLOW}{Fore.BLACK} EAC STATUS CHANGE DETECTED {Style.RESET_ALL}")
                    print(f"   Changed from: {self.last_eac_status} → {current_status}")
                
                self.last_eac_status = current_status
            else:
                print(f"{Fore.YELLOW}EAC status not found in components{Style.RESET_ALL}")
        
        # Check incidents for EAC-related issues
        incidents_data = self.make_request(EPIC_INCIDENTS_URL)
        if incidents_data:
            incidents = incidents_data.get("incidents", [])
            eac_incidents = []
            
            for incident in incidents:
                name = incident.get("name", "").lower()
                updates = incident.get("incident_updates", [])
                
                if any(keyword in name for keyword in ["anti", "cheat", "eac", "anticheat"]):
                    eac_incidents.append(incident)
                    continue
                
                # Check incident updates for EAC mentions
                for update in updates:
                    body = update.get("body", "").lower()
                    if any(keyword in body for keyword in ["anti", "cheat", "eac", "anticheat"]):
                        eac_incidents.append(incident)
                        break
            
            if eac_incidents:
                print(f"\n{Fore.RED}EAC-Related Incidents Found:{Style.RESET_ALL}")
                for incident in eac_incidents[:3]:
                    print(f"  - {incident.get('name', 'Unknown Incident')}")
                    print(f"    Status: {incident.get('status', 'unknown').title()}")
            else:
                print(f"{Fore.GREEN}No EAC-related incidents detected{Style.RESET_ALL}")

    def display_incident_reports(self):
        """Display comprehensive incident reports"""
        print(f"\n{Back.RED}{Fore.WHITE} INCIDENT REPORTS {Style.RESET_ALL}")
        print("─" * 70)
        
        incidents_data = self.make_request(EPIC_INCIDENTS_URL)
        if not incidents_data:
            print(f"{Fore.RED}Unable to fetch incidents{Style.RESET_ALL}")
            return

        incidents = incidents_data.get("incidents", [])
        active_incidents = [i for i in incidents if not i.get("resolved_at") and i.get("status") != "resolved"]

        if not active_incidents:
            print(f"{Fore.GREEN}No active incidents reported{Style.RESET_ALL}")
        else:
            for idx, incident in enumerate(active_incidents[:5]):
                impact = incident.get("impact", "unknown").upper()
                impact_color = Fore.RED if impact == "CRITICAL" else Fore.YELLOW if impact == "MAJOR" else Fore.BLUE
                
                if impact == "CRITICAL":
                    print(f"\n{Back.RED}{Fore.WHITE} CRITICAL INCIDENT {Style.RESET_ALL}")
                elif impact == "MAJOR":
                    print(f"\n{Back.YELLOW}{Fore.BLACK} MAJOR INCIDENT {Style.RESET_ALL}")
                else:
                    print()
                
                print(f"{Fore.WHITE}{incident.get('name', 'Unknown Incident')}{Style.RESET_ALL}")
                print(f"   Status: {impact_color}{incident.get('status', 'unknown').title()}{Style.RESET_ALL}")
                print(f"   Impact: {impact_color}{impact}{Style.RESET_ALL}")
                print(f"   Started: {Fore.LIGHTBLACK_EX}{incident.get('created_at', 'Unknown')}{Style.RESET_ALL}")
                
                # Latest update
                updates = incident.get("incident_updates", [])
                if updates:
                    latest = updates[0]
                    print(f"   Latest: {Fore.CYAN}{latest.get('body', 'No details')[:100]}{'...' if len(latest.get('body', '')) > 100 else ''}{Style.RESET_ALL}")

        # Show recent resolved incidents from the main incidents endpoint
        resolved_incidents = [i for i in incidents if i.get("resolved_at") or i.get("status") == "resolved"]
        recent_resolved = sorted(resolved_incidents, key=lambda x: x.get("resolved_at", ""), reverse=True)[:3]
        
        if recent_resolved:
            print(f"\n{Fore.CYAN}Recently Resolved Incidents:{Style.RESET_ALL}")
            for incident in recent_resolved:
                print(f"  - {incident.get('name', 'Unknown')}")
                resolved_time = incident.get('resolved_at', 'Unknown')
                if resolved_time and resolved_time != 'Unknown':
                    try:
                        # Parse and format the timestamp
                        dt = datetime.fromisoformat(resolved_time.replace('Z', '+00:00'))
                        formatted_time = dt.strftime('%Y-%m-%d %H:%M UTC')
                        print(f"    Resolved: {Fore.GREEN}{formatted_time}{Style.RESET_ALL}")
                    except:
                        print(f"    Resolved: {Fore.GREEN}{resolved_time}{Style.RESET_ALL}")

    def display_free_games(self):
        """Display current free games and promotions"""
        print(f"\n{Back.GREEN}{Fore.WHITE} FREE GAMES & PROMOTIONS {Style.RESET_ALL}")
        print("─" * 70)
        
        free_games_data = self.make_request(EPIC_FREE_GAMES_URL)
        if not free_games_data:
            print(f"{Fore.RED}Unable to fetch free games data{Style.RESET_ALL}")
            return

        games = free_games_data.get("data", {}).get("Catalog", {}).get("searchStore", {}).get("elements", [])
        current_time = datetime.now(timezone.utc)
        
        free_games = []
        upcoming_games = []
        
        for game in games:
            if not game.get("promotions"):
                continue
                
            promotional_offers = game.get("promotions", {}).get("promotionalOffers", [])
            upcoming_offers = game.get("promotions", {}).get("upcomingPromotionalOffers", [])
            
            # Check current free games
            for offer_set in promotional_offers:
                for offer in offer_set.get("promotionalOffers", []):
                    discount_pct = offer.get("discountSetting", {}).get("discountPercentage", 0)
                    if discount_pct == 0:  # Free game
                        end_date = offer.get("endDate")
                        if end_date:
                            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                            if end_dt > current_time:
                                free_games.append((game, end_dt))
            
            # Check upcoming free games
            for offer_set in upcoming_offers:
                for offer in offer_set.get("promotionalOffers", []):
                    discount_pct = offer.get("discountSetting", {}).get("discountPercentage", 0)
                    if discount_pct == 0:  # Free game
                        start_date = offer.get("startDate")
                        if start_date:
                            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                            upcoming_games.append((game, start_dt))

        # Display current free games
        if free_games:
            print(f"{Fore.GREEN}Currently FREE:{Style.RESET_ALL}")
            for game, end_date in free_games:
                title = game.get("title", "Unknown Game")
                description = game.get("description", "")[:60] + "..." if len(game.get("description", "")) > 60 else game.get("description", "")
                days_left = (end_date - current_time).days
                hours_left = (end_date - current_time).seconds // 3600
                
                print(f"  {Fore.CYAN}{title}{Style.RESET_ALL}")
                print(f"     {Fore.LIGHTBLACK_EX}{description}{Style.RESET_ALL}")
                
                if days_left > 0:
                    print(f"     Ends in {Fore.YELLOW}{days_left} days{Style.RESET_ALL} ({end_date.strftime('%Y-%m-%d %H:%M UTC')})")
                else:
                    print(f"     Ends in {Fore.RED}{hours_left} hours{Style.RESET_ALL} ({end_date.strftime('%Y-%m-%d %H:%M UTC')})")
                print()
        else:
            print(f"{Fore.YELLOW}No free games currently available{Style.RESET_ALL}")

        # Display upcoming free games
        if upcoming_games:
            print(f"{Fore.BLUE}Coming Soon:{Style.RESET_ALL}")
            for game, start_date in upcoming_games[:3]:  # Limit to next 3
                title = game.get("title", "Unknown Game")
                days_until = (start_date - current_time).days
                print(f"  {Fore.MAGENTA}{title}{Style.RESET_ALL} - Starts in {Fore.CYAN}{days_until} days{Style.RESET_ALL}")

    def display_api_status(self):
        """Display which API endpoints are working"""
        print(f"\n{Back.YELLOW}{Fore.BLACK} API STATUS & INFO {Style.RESET_ALL}")
        print("─" * 70)
        
        endpoints = [
            ("Summary API", EPIC_STATUS_URL),
            ("Status API", EPIC_STATUS_CURRENT),
            ("Incidents API", EPIC_INCIDENTS_URL),
            ("Components API", EPIC_COMPONENTS_URL),
            ("Free Games API", EPIC_FREE_GAMES_URL)
        ]
        
        working_count = 0
        for name, url in endpoints:
            # Quick check without full parsing
            try:
                response = requests.head(url, headers=HEADERS, timeout=10)
                if response.status_code == 200:
                    print(f"  {Fore.GREEN}✓{Style.RESET_ALL} {name}")
                    working_count += 1
                else:
                    print(f"  {Fore.RED}✗{Style.RESET_ALL} {name} (HTTP {response.status_code})")
            except:
                print(f"  {Fore.RED}✗{Style.RESET_ALL} {name} (Connection Error)")
        
        print(f"\n{Fore.CYAN}{working_count}/{len(endpoints)} API endpoints operational{Style.RESET_ALL}")
        
        if working_count < len(endpoints):
            print(f"{Fore.YELLOW}Note: Some Epic Games API endpoints appear to have been removed or changed.{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}This is common as companies update their APIs. The script has been updated to use working endpoints.{Style.RESET_ALL}")

    def display_footer(self, next_check: int):
        """Display footer with next check info"""
        print(f"\n{Fore.WHITE}{'─' * 70}{Style.RESET_ALL}")
        print(f"{Fore.LIGHTBLACK_EX}Last updated: {self.timestamp()}{Style.RESET_ALL}")
        if next_check > 0:
            print(f"{Fore.CYAN}Next check in {next_check} seconds... (Press Ctrl+C to exit){Style.RESET_ALL}")
        print(f"{Fore.WHITE}{'─' * 70}{Style.RESET_ALL}\n")

    def run_single_check(self):
        """Run a single comprehensive check"""
        self.print_banner()
        self.display_system_status()
        self.display_components_detailed()
        self.display_easy_anticheat_status()
        self.display_incident_reports()
        self.display_free_games()
        self.display_api_status()

    def run_monitoring(self, poll_interval: int = 300):  # Default 5 minutes
        """Run continuous monitoring"""
        try:
            while True:
                # Clear screen (works on most terminals)
                print("\033[2J\033[H")
                
                self.run_single_check()
                self.display_footer(poll_interval)
                
                if poll_interval > 0:
                    time.sleep(poll_interval)
                else:
                    break
                    
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}Monitoring stopped by user. Goodbye!{Style.RESET_ALL}")
            sys.exit(0)
        except Exception as e:
            print(f"\n{Fore.RED}Unexpected error: {e}{Style.RESET_ALL}")
            sys.exit(1)

def main():
    """Main entry point"""
    monitor = EpicGamesMonitor()
    
    # Parse command line arguments
    if len(sys.argv) >= 2:
        if sys.argv[1] in ['-h', '--help', 'help']:
            print(f"""
{Fore.CYAN}Epic Games Monitor v3.1 (Fixed Version){Style.RESET_ALL}

Usage:
  python3 {sys.argv[0]} [interval]
  python3 {sys.argv[0]} --once
  python3 {sys.argv[0]} --help

Arguments:
  interval    Seconds between checks (default: 300)
  --once      Run once and exit
  --help      Show this help message

Features:
  - System Status Monitoring
  - Detailed Components List (replaces removed Services API)
  - Easy Anti-Cheat Status Tracking
  - Comprehensive Incident Reports
  - Free Games & Promotions
  - API Health Monitoring

Changes in v3.1:
  - Removed defunct API endpoints (services, maintenance, news, history)
  - Added detailed components view
  - Improved error handling
  - Added API status monitoring

Examples:
  python3 {sys.argv[0]}           # Monitor with 5-minute intervals
  python3 {sys.argv[0]} 60        # Monitor with 1-minute intervals
  python3 {sys.argv[0]} --once    # Single check and exit
            """)
            return
        elif sys.argv[1] == '--once':
            monitor.run_single_check()
            return
        else:
            try:
                interval = int(sys.argv[1])
                if interval < 10:
                    print(f"{Fore.YELLOW}Minimum interval is 10 seconds to avoid rate limiting{Style.RESET_ALL}")
                    interval = 10
                monitor.run_monitoring(interval)
            except ValueError:
                print(f"{Fore.RED}Invalid interval. Using default of 300 seconds.{Style.RESET_ALL}")
                monitor.run_monitoring()
    else:
        monitor.run_monitoring()

if __name__ == "__main__":
    main()