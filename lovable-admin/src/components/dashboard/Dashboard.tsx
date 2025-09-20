import { StatsCard } from "./StatsCard";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Music, Users, Album, TrendingUp, Plus, Search } from "lucide-react";

interface DashboardProps {
  onPageChange: (page: string) => void;
}

export function Dashboard({ onPageChange }: DashboardProps) {
  // Mock data - replace with actual API calls
  const stats = [
    {
      title: "Total Mele (Songs)",
      value: "2,847",
      icon: Music,
      gradient: "from-ocean-deep to-ocean-light",
      description: "Hawaiian songs in database"
    },
    {
      title: "Artists",
      value: "486",
      icon: Users,
      gradient: "from-coral to-sunset",
      description: "Musicians and composers"
    },
    {
      title: "Albums",
      value: "234",
      icon: Album,
      gradient: "from-tropical to-tropical-light",
      description: "Music collections"
    },
    {
      title: "Recent Additions",
      value: "23",
      icon: TrendingUp,
      gradient: "from-ocean-light to-tropical",
      description: "Added this month"
    }
  ];

  const recentActivity = [
    { action: "Added new mele", item: "'Aloha 'Oe' by Queen Lili'uokalani", time: "2 hours ago" },
    { action: "Updated artist", item: "Israel Kamakawiwoʻole profile", time: "5 hours ago" },
    { action: "New album entry", item: "'Facing Future' collection", time: "1 day ago" },
    { action: "Added lyrics", item: "'White Sandy Beach' translation", time: "2 days ago" }
  ];

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Aloha! Welcome to Huapala</h1>
          <p className="text-muted-foreground">Manage your Hawaiian music database</p>
        </div>
        <div className="flex gap-2">
          <Button 
            onClick={() => onPageChange("add")}
            className="bg-gradient-to-r from-ocean-deep to-ocean-light hover:from-ocean-light hover:to-tropical shadow-ocean"
          >
            <Plus className="h-4 w-4 mr-2" />
            Add Entry
          </Button>
          <Button 
            variant="outline"
            onClick={() => onPageChange("search")}
            className="border-ocean-light text-ocean-deep hover:bg-ocean-light/10"
          >
            <Search className="h-4 w-4 mr-2" />
            Search
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat, index) => (
          <StatsCard key={index} {...stat} />
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-ocean-deep" />
              Recent Activity
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {recentActivity.map((activity, index) => (
                <div key={index} className="flex items-start gap-3 p-3 rounded-lg bg-accent/30 hover:bg-accent/50 transition-colors">
                  <div className="w-2 h-2 rounded-full bg-coral mt-2"></div>
                  <div className="flex-1">
                    <p className="text-sm font-medium">{activity.action}</p>
                    <p className="text-sm text-muted-foreground">{activity.item}</p>
                    <p className="text-xs text-muted-foreground mt-1">{activity.time}</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Music className="h-5 w-5 text-tropical" />
              Quick Actions
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <Button 
              variant="outline" 
              className="w-full justify-start gap-3 border-ocean-light text-ocean-deep hover:bg-ocean-light/10"
              onClick={() => onPageChange("songs")}
            >
              <Music className="h-4 w-4" />
              Browse All Mele
            </Button>
            <Button 
              variant="outline" 
              className="w-full justify-start gap-3 border-coral text-coral hover:bg-coral-light/10"
              onClick={() => onPageChange("artists")}
            >
              <Users className="h-4 w-4" />
              Manage Artists
            </Button>
            <Button 
              variant="outline" 
              className="w-full justify-start gap-3 border-tropical text-tropical hover:bg-tropical-light/10"
              onClick={() => onPageChange("add")}
            >
              <Plus className="h-4 w-4" />
              Add New Entry
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}