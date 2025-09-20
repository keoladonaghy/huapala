import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Music, Database, Search, Plus, Settings } from "lucide-react";

interface NavigationProps {
  currentPage: string;
  onPageChange: (page: string) => void;
}

export function Navigation({ currentPage, onPageChange }: NavigationProps) {
  const navItems = [
    { id: "dashboard", label: "Dashboard", icon: Database },
    { id: "songs", label: "Mele (Songs)", icon: Music },
    { id: "artists", label: "Artists", icon: Music },
    { id: "search", label: "Search", icon: Search },
    { id: "add", label: "Add Entry", icon: Plus },
    { id: "settings", label: "Settings", icon: Settings },
  ];

  return (
    <nav className="w-64 bg-card border-r border-border min-h-screen p-4">
      <div className="mb-8">
        <h1 className="text-2xl font-bold bg-gradient-to-r from-ocean-deep to-tropical bg-clip-text text-transparent">
          Huapala
        </h1>
        <p className="text-sm text-muted-foreground">Hawaiian Music Database</p>
      </div>
      
      <div className="space-y-2">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <Button
              key={item.id}
              variant={currentPage === item.id ? "default" : "ghost"}
              className={cn(
                "w-full justify-start gap-3",
                currentPage === item.id && "bg-gradient-to-r from-ocean-deep to-ocean-light text-white shadow-ocean"
              )}
              onClick={() => onPageChange(item.id)}
            >
              <Icon className="h-4 w-4" />
              {item.label}
            </Button>
          );
        })}
      </div>
    </nav>
  );
}