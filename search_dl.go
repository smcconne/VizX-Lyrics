package main

import (
	"bufio"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strconv"
	"strings"

	"main/utils/ampapi"
	"main/utils/structs"

	"github.com/fatih/color"
	"gopkg.in/yaml.v2"
)

var (
	cTitle   = color.New(color.FgCyan, color.Bold)
	cHeader  = color.New(color.FgHiBlue, color.Bold)
	cPrompt  = color.New(color.FgGreen, color.Bold)
	cAccent  = color.New(color.FgYellow)
	cSuccess = color.New(color.FgGreen)
	cError   = color.New(color.FgRed, color.Bold)
	cMuted   = color.New(color.FgHiBlack)
	cLink    = color.New(color.FgBlue, color.Underline)
	cSong    = color.New(color.FgWhite, color.Bold)
	cArtist  = color.New(color.FgGreen)
	cAlbum   = color.New(color.FgYellow)
)

var Config structs.ConfigSet

func loadConfig() error {
	exePath, err := os.Executable()
	var workingDir string
	if err == nil {
		workingDir = filepath.Dir(exePath)
	} else {
		workingDir = "."
	}
	
	configPath := filepath.Join(workingDir, "config.yaml")
	data, err := os.ReadFile(configPath)
	if err != nil {
		return err
	}
	err = yaml.Unmarshal(data, &Config)
	if err != nil {
		return err
	}
	if len(Config.Storefront) != 2 {
		Config.Storefront = "us"
	}
	return nil
}

func readInput(prompt string) string {
	cPrompt.Print(prompt)
	reader := bufio.NewReader(os.Stdin)
	text, _ := reader.ReadString('\n')
	return strings.TrimSpace(text)
}

func padRight(s string, length int) string {
	runes := []rune(s)
	if len(runes) > length {
		if length > 3 {
			return string(runes[:length-3]) + "..."
		}
		return string(runes[:length])
	}
	return s + strings.Repeat(" ", length-len(runes))
}

func printRow(id, title, artist, album string, isHeader bool) {
	idCol := padRight(id, 6)
	titleCol := padRight(title, 30)
	artistCol := padRight(artist, 22)
	albumCol := padRight(album, 22)

	if isHeader {
		cHeader.Printf("  %s %s %s %s\n", idCol, titleCol, artistCol, albumCol)
	} else {
		fmt.Printf("  %s %s %s %s\n",
			cAccent.Sprint(idCol),
			cSong.Sprint(titleCol),
			cArtist.Sprint(artistCol),
			cMuted.Sprint(albumCol),
		)
	}
}

func downloadLink(link string) {
	exePath, err := os.Executable()
	var workingDir string
	var dlCmd string = "./dl"
	if err == nil {
		workingDir = filepath.Dir(exePath)
		dlCmd = filepath.Join(workingDir, "dl")
	}

	cSuccess.Printf("\n🚀 Launching downloader: %s %s\n", dlCmd, link)
	cmd := exec.Command(dlCmd, link)
	if workingDir != "" {
		cmd.Dir = workingDir
	}
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	cmd.Stdin = os.Stdin
	err = cmd.Run()
	if err != nil {
		cError.Printf("❌ Error executing download script: %v\n", err)
	}
}

func main() {
	err := loadConfig()
	if err != nil {
		cError.Printf("Failed to load config: %v\n", err)
		os.Exit(1)
	}

	token, err := ampapi.GetToken()
	if err != nil {
		if Config.AuthorizationToken != "" && Config.AuthorizationToken != "your-authorization-token" {
			token = strings.Replace(Config.AuthorizationToken, "Bearer ", "", -1)
		} else {
			cError.Printf("Failed to retrieve Apple Music token: %v\n", err)
			os.Exit(1)
		}
	}

	var query string
	if len(os.Args) > 1 {
		query = strings.Join(os.Args[1:], " ")
	} else {
		query = readInput("❯ Enter song name to search: ")
	}

	if query == "" {
		cError.Println("❌ No search query provided. Exiting.")
		return
	}

	fmt.Println()
	cTitle.Printf("🔍 Searching Apple Music for: %q...\n", query)
	searchResp, err := ampapi.Search(Config.Storefront, query, "songs", Config.Language, token, 20, 0)
	if err != nil {
		cError.Printf("❌ Search query failed: %v\n", err)
		os.Exit(1)
	}

	if searchResp.Results.Songs == nil || len(searchResp.Results.Songs.Data) == 0 {
		cError.Println("❌ No songs found matching that search query.")
		return
	}

	fmt.Println()
	cTitle.Println("  ===============================================================================")
	cTitle.Println("                           APPLE MUSIC SEARCH RESULTS                            ")
	cTitle.Println("  ===============================================================================")
	fmt.Println()
	
	printRow("ID", "TITLE", "ARTIST", "ALBUM", true)
	cHeader.Println("  -------------------------------------------------------------------------------")

	for i, song := range searchResp.Results.Songs.Data {
		idxStr := fmt.Sprintf("[%d]", i+1)
		printRow(idxStr, song.Attributes.Name, song.Attributes.ArtistName, song.Attributes.AlbumName, false)
	}
	cHeader.Println("  -------------------------------------------------------------------------------")

	var selectedIndex int
	for {
		choice := readInput(fmt.Sprintf("\n❯ Select a song number (1-%d): ", len(searchResp.Results.Songs.Data)))
		idx, err := strconv.Atoi(choice)
		if err == nil && idx >= 1 && idx <= len(searchResp.Results.Songs.Data) {
			selectedIndex = idx - 1
			break
		}
		cError.Println("❌ Invalid selection. Please enter a valid number.")
	}

	selectedSong := searchResp.Results.Songs.Data[selectedIndex]
	
	var albumId string
	if len(selectedSong.Relationships.Albums.Data) > 0 {
		albumId = selectedSong.Relationships.Albums.Data[0].ID
	}

	var albumResp *ampapi.AlbumResp
	if albumId != "" {
		albumResp, err = ampapi.GetAlbumResp(Config.Storefront, albumId, Config.Language, token)
	}

	if err != nil || albumResp == nil || len(albumResp.Data) == 0 {
		fmt.Println()
		cTitle.Println("  -------------------------------------------------------------------------------")
		fmt.Printf("    %s   %s\n", cAccent.Sprint("Song:  "), cSong.Sprint(selectedSong.Attributes.Name))
		fmt.Printf("    %s %s\n", cAccent.Sprint("Artist:"), cArtist.Sprint(selectedSong.Attributes.ArtistName))
		fmt.Printf("    %s   %s\n", cAccent.Sprint("Link:  "), cLink.Sprint(selectedSong.Attributes.URL))
		cTitle.Println("  -------------------------------------------------------------------------------")
		fmt.Println()
		
		confirm := readInput("❯ Proceed with downloading this song? (y/n): ")
		if strings.ToLower(confirm) == "y" || strings.ToLower(confirm) == "yes" {
			downloadLink(selectedSong.Attributes.URL)
		} else {
			cAccent.Println("Download cancelled.")
		}
		return
	}

	album := albumResp.Data[0]
	tracks := album.Relationships.Tracks.Data

	if len(tracks) > 1 {
		fmt.Println()
		cTitle.Println("  ===============================================================================")
		cTitle.Printf("   ALBUM:  %s\n", album.Attributes.Name)
		cTitle.Printf("   ARTIST: %s (%d tracks)\n", album.Attributes.ArtistName, len(tracks))
		cTitle.Println("  ===============================================================================")
		fmt.Println()

		for i, track := range tracks {
			fmt.Printf("    %s %s\n", cAccent.Sprintf("%2d.", i+1), cSong.Sprint(track.Attributes.Name))
		}
		fmt.Println()
		cAccent.Println("    [A] Download Whole Album")
		fmt.Println()

		for {
			choice := readInput("❯ Enter track number to download, or 'A' to download the whole album: ")
			choiceLower := strings.ToLower(choice)
			if choiceLower == "a" {
				cSuccess.Printf("📥 Downloading whole album: %s\n", album.Attributes.Name)
				downloadLink(album.Attributes.URL)
				break
			}
			idx, err := strconv.Atoi(choice)
			if err == nil && idx >= 1 && idx <= len(tracks) {
				selectedTrack := tracks[idx-1]
				cSuccess.Printf("📥 Downloading track: %s\n", selectedTrack.Attributes.Name)
				downloadLink(selectedTrack.Attributes.URL)
				break
			}
			cError.Println("❌ Invalid input. Please choose a valid track number or 'A'.")
		}
	} else {
		// Single song album
		fmt.Println()
		cTitle.Println("  -------------------------------------------------------------------------------")
		fmt.Printf("    %s   %s\n", cAccent.Sprint("Song:  "), cSong.Sprint(selectedSong.Attributes.Name))
		fmt.Printf("    %s %s\n", cAccent.Sprint("Artist:"), cArtist.Sprint(selectedSong.Attributes.ArtistName))
		fmt.Printf("    %s  %s\n", cAccent.Sprint("Album: "), cAlbum.Sprint(selectedSong.Attributes.AlbumName))
		fmt.Printf("    %s   %s\n", cAccent.Sprint("Link:  "), cLink.Sprint(selectedSong.Attributes.URL))
		cTitle.Println("  -------------------------------------------------------------------------------")
		fmt.Println()
		
		confirm := readInput("❯ Proceed with downloading? (y/n): ")
		if strings.ToLower(confirm) == "y" || strings.ToLower(confirm) == "yes" {
			downloadLink(selectedSong.Attributes.URL)
		} else {
			cAccent.Println("Download cancelled.")
		}
	}
}
