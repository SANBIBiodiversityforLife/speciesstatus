function insertLogos() {
  names = {'adu': 'Animal Demographic Unit',
      'blsa': 'Birdlife South Africa',
      'dea': 'Department of Environmental Affairs',
      'ewt': 'Endangered Wildlife Trust',
      'esk': 'Eskom ',
      'iucna': 'IUCN Amphibian Specialist Group',
      'iucnd': 'IUCN Dragonfly Specialist Group',
      'iucnf': 'IUCN Freshwater Fish Specialist Group',
      'jrs': 'JRS Biodiversity Foundation',
      'mon': 'MONDI',
      'nrf': 'National Research Foundation',
      'norw': 'Norwegian  Ministry of Foreign Affairs ',
      'saft': 'SAFTRONICS',
      'saiab': 'SAIAB',
      'sanbi': 'SANBI',
      'lep': 'The Lepidopterists Society of Africa',
      'omt': 'The Oppenheimer Memorial Trust',
      'stel': 'University of Stellenbosch',
      'eos': 'E Oppenheimer & Son ',
      'beers': 'De Beers Group of Companies',
      'uct': 'University of Cape Town',
      'ori': 'Oceanographic Research Institute, Durban',
      'daff': 'Department of Agriculture, Forestry and Fisheries'}

  logos = {'Amphibia': {'lead': ['iucna'], 'funder': ['sanbi', 'norw']},
       'Lepidoptera': {'lead': ['adu'], 'funder': ['sanbi', 'dea', 'norw', 'omt', 'saft'], 'partner': ['lep']},
       'Reptilia': {'lead': ['adu'], 'funder': ['sanbi', 'dea', 'norw']},
       'Odonata': {'lead': ['stel'], 'funder': ['mondi', 'jrs', 'nrf'], 'partner': ['iucnd']},
       'Aves': {'lead': ['blsa'], 'funder': ['esk', 'sanbi'], 'partner': ['adu']},
       'Mammalia': {'lead': ['ewt'], 'funder': ['norw', 'sanbi'], 'partner': ['sanbi']},
       'Elasmobranchii': {'lead': ['sanbi'], 'funder': ['norw'], 'partner': ['uct', 'ori', 'daff']},
       'Actinopterygii': {'lead': ['sanbi'], 'funder': ['norw'], 'partner': ['uct', 'ori', 'daff']},
       'Holocephali': {'lead': ['sanbi'], 'funder': ['norw'], 'partner': ['uct', 'ori', 'daff']}}

  // A template image we just have so we can get the static path to replace it to build logo urls
  var templateImageSrc = $('.assessment-aside img').first().attr('src');

  // Loop through the ancestry tree
  $('#breadcrumb').children('a').each(function() {
    var taxonNode = $(this).text();

    // Try and find some logo rules, break out of for loop once we find some
    if(taxonNode in logos) {
      var logoSet = logos[taxonNode];

      // Find and add the images under the lead, funder and partner headings
      var logoImgs = '';
      $.each(logoSet['lead'], (function(){ logoImgs += '<img src="' + templateImageSrc.replace('adu', this) + '" alt="Lead">'; }));
      $('.lead').after(logoImgs);

      logoImgs = '';
      $.each(logoSet['funder'], (function(){ logoImgs += '<img src="' + templateImageSrc.replace('adu', this) + '" alt="Funder">'; }));
      $('.funder').after(logoImgs);

      if('partner' in logoSet) {
        logoImgs = '';
        $.each(logoSet['partner'], (function(){ logoImgs += '<img src="' + templateImageSrc.replace('adu', this) + '" alt="Partner">'; }));
        $('.partner').after(logoImgs);
      } else {
        $('.partner').hide();
      }

      return false;
    }
  });

};