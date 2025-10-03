import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Search, Music, Edit, Eye, Filter } from "lucide-react";

interface Song {
  id: string;
  title: string;
  englishTitle?: string;
  composer: string;
  year?: number;
  genre: string;
  isHawaiian: boolean;
  hasLyrics: boolean;
  hasTranslation: boolean;
}

export function SongsList() {
  const [searchTerm, setSearchTerm] = useState("");
  const [filterGenre, setFilterGenre] = useState("all");

  // Mock data - replace with API calls
  const songs: Song[] = [
    {
      id: "1",
      title: "Aloha 'Oe",
      englishTitle: "Farewell to You",
      composer: "Queen Lili'uokalani",
      year: 1878,
      genre: "Traditional",
      isHawaiian: true,
      hasLyrics: true,
      hasTranslation: true
    },
    {
      id: "2",
      title: "White Sandy Beach",
      composer: "Israel Kamakawiwoʻole",
      year: 1993,
      genre: "Contemporary",
      isHawaiian: false,
      hasLyrics: true,
      hasTranslation: false
    },
    {
      id: "3",
      title: "Hawaiian Wedding Song",
      englishTitle: "Ke Kali Nei Au",
      composer: "Charles E. King",
      year: 1926,
      genre: "Traditional",
      isHawaiian: true,
      hasLyrics: true,
      hasTranslation: true
    },
    {
      id: "4",
      title: "Somewhere Over the Rainbow",
      composer: "Israel Kamakawiwoʻole",
      year: 1993,
      genre: "Cover",
      isHawaiian: false,
      hasLyrics: true,
      hasTranslation: false
    }
  ];

  const filteredSongs = songs.filter(song => {
    const matchesSearch = song.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         song.composer.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         (song.englishTitle && song.englishTitle.toLowerCase().includes(searchTerm.toLowerCase()));
    
    const matchesFilter = filterGenre === "all" || song.genre.toLowerCase() === filterGenre.toLowerCase();
    
    return matchesSearch && matchesFilter;
  });

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Mele (Songs)</h1>
          <p className="text-muted-foreground">Browse and manage Hawaiian music collection</p>
        </div>
      </div>

      <Card>
        <CardHeader>
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search by title, composer, or English title..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            <div className="flex gap-2">
              <Button
                variant={filterGenre === "all" ? "default" : "outline"}
                size="sm"
                onClick={() => setFilterGenre("all")}
                className={filterGenre === "all" ? "bg-ocean-deep text-white" : ""}
              >
                All
              </Button>
              <Button
                variant={filterGenre === "traditional" ? "default" : "outline"}
                size="sm"
                onClick={() => setFilterGenre("traditional")}
                className={filterGenre === "traditional" ? "bg-ocean-deep text-white" : ""}
              >
                Traditional
              </Button>
              <Button
                variant={filterGenre === "contemporary" ? "default" : "outline"}
                size="sm"
                onClick={() => setFilterGenre("contemporary")}
                className={filterGenre === "contemporary" ? "bg-ocean-deep text-white" : ""}
              >
                Contemporary
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {filteredSongs.map((song) => (
              <div
                key={song.id}
                className="flex items-center justify-between p-4 border border-border rounded-lg hover:bg-accent/30 transition-colors"
              >
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <Music className="h-4 w-4 text-ocean-deep" />
                    <h3 className="font-semibold text-foreground">{song.title}</h3>
                    {song.englishTitle && (
                      <span className="text-sm text-muted-foreground">({song.englishTitle})</span>
                    )}
                  </div>
                  <p className="text-sm text-muted-foreground mb-2">
                    Composed by {song.composer} {song.year && `• ${song.year}`}
                  </p>
                  <div className="flex items-center gap-2">
                    <Badge variant={song.isHawaiian ? "default" : "secondary"} className={song.isHawaiian ? "bg-ocean-deep" : ""}>
                      {song.genre}
                    </Badge>
                    {song.isHawaiian && (
                      <Badge variant="outline" className="border-tropical text-tropical">
                        Hawaiian
                      </Badge>
                    )}
                    {song.hasLyrics && (
                      <Badge variant="outline" className="border-coral text-coral">
                        Lyrics
                      </Badge>
                    )}
                    {song.hasTranslation && (
                      <Badge variant="outline" className="border-sunset text-sunset">
                        Translation
                      </Badge>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Button size="sm" variant="outline" className="border-ocean-light text-ocean-deep hover:bg-ocean-light/10">
                    <Eye className="h-4 w-4" />
                  </Button>
                  <Button size="sm" variant="outline" className="border-tropical text-tropical hover:bg-tropical-light/10">
                    <Edit className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
          
          {filteredSongs.length === 0 && (
            <div className="text-center py-8">
              <Music className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <p className="text-muted-foreground">No songs found matching your search criteria.</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}