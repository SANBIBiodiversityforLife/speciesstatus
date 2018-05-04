SELECT taxon.name, assess.id, bib.*
FROM taxa_taxon taxon
JOIN redlist_assessment assess
ON taxon.id = assess.taxon_id
JOIN redlist_assessment_references ref ON 
assess.id = ref.assessment_id
JOIN biblio_reference bib ON
bib.id = ref.reference_id
WHERE taxon.name ILIKE 'xen%'
