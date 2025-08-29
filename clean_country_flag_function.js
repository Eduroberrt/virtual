    getCountryFlag(countryCode) {
        // Convert to lowercase and remove spaces for matching
        const normalizedCode = countryCode.toLowerCase().replace(/\s+/g, '');
        
        // Simple flag mapping for most common countries
        const countryNameToFlag = {
            'afghanistan': '🇦🇫', 'albania': '🇦🇱', 'algeria': '🇩🇿', 'angola': '🇦🇴',
            'argentina': '🇦🇷', 'armenia': '🇦🇲', 'australia': '🇦🇺', 'austria': '🇦🇹',
            'azerbaijan': '🇦🇿', 'bahrain': '🇧🇭', 'bangladesh': '🇧🇩', 'belarus': '🇧🇾',
            'belgium': '🇧🇪', 'bolivia': '🇧🇴', 'brazil': '🇧🇷', 'bulgaria': '🇧🇬',
            'cambodia': '🇰🇭', 'cameroon': '🇨🇲', 'canada': '🇨🇦', 'chile': '🇨🇱',
            'china': '🇨🇳', 'colombia': '🇨🇴', 'croatia': '🇭🇷', 'czech': '🇨🇿',
            'denmark': '🇩🇰', 'ecuador': '🇪🇨', 'egypt': '🇪🇬', 'estonia': '🇪🇪',
            'finland': '🇫🇮', 'france': '🇫🇷', 'georgia': '🇬🇪', 'germany': '🇩🇪',
            'ghana': '🇬🇭', 'greece': '🇬🇷', 'guatemala': '🇬🇹', 'honduras': '🇭🇳',
            'hungary': '🇭🇺', 'india': '🇮🇳', 'indonesia': '🇮🇩', 'ireland': '🇮🇪',
            'israel': '🇮🇱', 'italy': '🇮🇹', 'japan': '🇯🇵', 'kazakhstan': '🇰🇿',
            'kenya': '🇰🇪', 'kuwait': '🇰🇼', 'latvia': '🇱🇻', 'lithuania': '🇱🇹',
            'malaysia': '🇲🇾', 'mexico': '🇲🇽', 'morocco': '🇲🇦', 'netherlands': '🇳🇱',
            'nigeria': '🇳🇬', 'norway': '🇳🇴', 'pakistan': '🇵🇰', 'philippines': '🇵🇭',
            'poland': '🇵🇱', 'portugal': '🇵🇹', 'romania': '🇷🇴', 'russia': '🇷🇺',
            'saudiarabia': '🇸🇦', 'singapore': '🇸🇬', 'southafrica': '🇿🇦', 'spain': '🇪🇸',
            'sweden': '🇸🇪', 'thailand': '🇹🇭', 'turkey': '🇹🇷', 'ukraine': '🇺🇦',
            'usa': '🇺🇸', 'vietnam': '🇻🇳', 'unitedkingdom': '🇬🇧', 'england': '🇬🇧'
        };
        
        return countryNameToFlag[normalizedCode] || '🌍';
    }
