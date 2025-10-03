// Example: How to display JSONB song data on the web

class SongRenderer {
    constructor(songData) {
        this.song = songData;
    }
    
    // Render complete song as HTML table (like original huapala.org)
    renderAsTable() {
        let html = `
            <div class="song-header">
                <h2>${this.song.title}</h2>
                <p class="composer">Composer: ${this.song.composer}</p>
                ${this.song.translator ? `<p class="translator">Translator: ${this.song.translator}</p>` : ''}
            </div>
            <table class="lyrics-table">
        `;
        
        this.song.sections.forEach(section => {
            // Add section header if needed
            if (section.type === 'chorus') {
                html += `
                    <tr class="section-header">
                        <td colspan="2"><strong>Hui (Chorus)</strong></td>
                    </tr>
                `;
            }
            
            // Add all lines in this section
            section.lines.forEach(line => {
                html += `
                    <tr class="lyric-line" data-line-id="${line.id}">
                        <td class="hawaiian">${line.hawaiian_text}</td>
                        <td class="english">${line.english_text}</td>
                    </tr>
                `;
            });
            
            // Add spacing between sections
            html += `<tr class="section-spacer"><td colspan="2">&nbsp;</td></tr>`;
        });
        
        html += `</table>`;
        return html;
    }
    
    // Render for hapa haole songs (mostly English)
    renderHapaHaole() {
        let html = `
            <div class="song-header">
                <h2>${this.song.title}</h2>
                <p class="composer">Composer: ${this.song.composer}</p>
            </div>
            <div class="lyrics-simple">
        `;
        
        this.song.sections.forEach(section => {
            html += `<div class="section ${section.type}">`;
            
            if (section.type === 'chorus') {
                html += `<h4>Chorus</h4>`;
            }
            
            section.lines.forEach(line => {
                // For hapa haole, show whichever text exists
                const text = line.english_text || line.hawaiian_text;
                html += `<div class="line" data-line-id="${line.id}">${text}</div>`;
            });
            
            html += `</div>`;
        });
        
        html += `</div>`;
        return html;
    }
    
    // Get specific line by ID for citations
    getLine(lineId) {
        for (const section of this.song.sections) {
            const line = section.lines.find(l => l.id === lineId);
            if (line) return line;
        }
        return null;
    }
    
    // Search within song
    searchText(query) {
        const results = [];
        const searchTerm = query.toLowerCase();
        
        this.song.sections.forEach(section => {
            section.lines.forEach(line => {
                if (line.hawaiian_text.toLowerCase().includes(searchTerm) ||
                    line.english_text.toLowerCase().includes(searchTerm)) {
                    results.push({
                        line_id: line.id,
                        section_type: section.type,
                        hawaiian: line.hawaiian_text,
                        english: line.english_text
                    });
                }
            });
        });
        
        return results;
    }
}

// Example API endpoint that would use JSONB
class SongAPI {
    
    // Get song with structured lyrics (single query!)
    async getSong(songId) {
        const result = await db.query(`
            SELECT 
                id,
                canonical_title_hawaiian,
                primary_composer,
                structured_lyrics,
                created_at,
                updated_at
            FROM canonical_mele 
            WHERE id = $1
        `, [songId]);
        
        if (result.rows.length === 0) {
            throw new Error('Song not found');
        }
        
        const row = result.rows[0];
        return {
            id: row.id,
            title: row.canonical_title_hawaiian,
            composer: row.primary_composer,
            lyrics: row.structured_lyrics, // This is our JSONB data
            metadata: {
                created: row.created_at,
                updated: row.updated_at
            }
        };
    }
    
    // Search songs by lyric content
    async searchSongs(query) {
        const result = await db.query(`
            SELECT 
                id,
                canonical_title_hawaiian,
                primary_composer,
                structured_lyrics -> 'song_type' as song_type
            FROM canonical_mele 
            WHERE structured_lyrics @@ plainto_tsquery('english', $1)
               OR structured_lyrics::text ILIKE $2
        `, [query, `%${query}%`]);
        
        return result.rows;
    }
    
    // Get all songs with choruses
    async getSongsWithChorus() {
        const result = await db.query(`
            SELECT id, canonical_title_hawaiian
            FROM canonical_mele 
            WHERE structured_lyrics -> 'metadata' ->> 'has_chorus' = 'true'
            ORDER BY canonical_title_hawaiian
        `);
        
        return result.rows;
    }
}

// Example usage:
/*
const songData = await songAPI.getSong(123);
const renderer = new SongRenderer(songData.lyrics);

// For bilingual songs
if (songData.lyrics.song_type === 'bilingual') {
    document.getElementById('song-container').innerHTML = renderer.renderAsTable();
}

// For hapa haole songs  
if (songData.lyrics.song_type === 'hapa_haole') {
    document.getElementById('song-container').innerHTML = renderer.renderHapaHaole();
}

// Get specific line for citation
const line = renderer.getLine('v1.3');
console.log(`Line v1.3: ${line.hawaiian_text} / ${line.english_text}`);

// Search within song
const results = renderer.searchText('aloha');
console.log('Lines containing "aloha":', results);
*/