from typing import Dict, List, Optional
from .base import DukeApiServiceBase
import os
import dotenv

dotenv.load_dotenv()

class CurriculumApiService(DukeApiServiceBase):
    def __init__(self, api_base_url, api_key: Optional[str] = None):
        super().__init__(api_base_url, api_key)
        # Load relevant metadata
        self.subjects = self.load_metadata('subjects')
        self.terms = ["1940 - 2025 Fall Term", "1910 - 2025 Spring Term", "1930 - 2025 Summer Term 2", "1925 - 2025 Summer Term 1"]
        
    def get_courses_by_subject(self, subject_code: str) -> List[Dict]:
        """
        Get courses for a specific subject
        
        Args:
            subject_code: The subject code (e.g., 'COMPSCI')
            
        Returns:
            List of course objects or empty list if not found
            
        """

        def extract_subject_course_info(api_response: dict) -> List[Dict]:
            """
            Extract relevant course information from the Duke API response
            
            Args:
                api_response: The full API response from Duke's course API
                
            Returns:
                List of simplified course objects with relevant fields
            """
            simplified_courses = []
        
            try:
                # Navigate to the course_summary list
                course_summaries = (api_response.get('ssr_get_courses_resp', {})
                                .get('course_search_result', {})
                                .get('subjects', {})
                                .get('subject', {})
                                .get('course_summaries', {})
                                .get('course_summary', []))
                
                # Extract relevant fields from each course
                for course in course_summaries:
                    simplified_course = {
                        'crse_id': course.get('crse_id'),
                        'effective_date': course.get('effdt'),
                        'crse_offer_nbr': course.get('crse_offer_nbr'),
                        'subject': course.get('subject'),
                        'subject_lov_descr': course.get('subject_lov_descr'),
                        'catalog_nbr': course.get('catalog_nbr'),
                        'course_title_long': course.get('course_title_long'),
                        'offered': course.get('ssr_crse_typoff_cd_lov_descr')
                    }
                    simplified_courses.append(simplified_course)
                    
            except Exception as e:
                print(f"Error extracting course information: {e}")
                
            return simplified_courses

        if subject_code not in self.subjects['subjects']:
            return []
        
        endpoint = f"curriculum/courses/subject/{subject_code}"
        api_response = self._make_request(endpoint)

        if not api_response:
            return []

        return extract_subject_course_info(api_response)

        
    def get_course_details(self, course_id: str, course_offer_number: str) -> Optional[Dict]:
        """
        Get detailed information about a specific course
        
        Args:
            course_id: The course ID
            
        Returns:
            Course details or None if not found
        """
        def extract_course_info(data):
            try:
                course = data["ssr_get_course_offering_resp"]["course_offering_result"]["course_offering"]
                terms = course.get("terms_offered", {}).get("term_offered", [])
                
                # Get latest term based on the 'strm' code (larger is more recent)
                last_term = max(terms, key=lambda x: int(x["strm"])) if terms else {}

                # Extract required fields
                extracted = {
                    "crse_id": course.get("crse_id"),
                    "crse_offer_nbr": course.get("crse_offer_nbr"),
                    "institution_lov_descr": course.get("institution_lov_descr"),
                    "subject": course.get("subject"),
                    "subject_lov_descr": course.get("subject_lov_descr"),
                    "catalog_nbr": course.get("catalog_nbr").strip() if course.get("catalog_nbr") else None,
                    "descrlong": course.get("descrlong"),
                    "course_title_long": course.get("course_title_long"),
                    "units_minimum": course.get("units_minimum"),
                    "units_maximum": course.get("units_maximum"),
                    "grading_basis_lov_descr": course.get("grading_basis_lov_descr"),
                    "consent_lov_descr": course.get("consent_lov_descr"),
                    "ssr_drop_consent_lov_descr": course.get("ssr_drop_consent_lov_descr"),
                    "acad_career_lov_descr": course.get("acad_career_lov_descr"),
                    "acad_group_lov_descr": course.get("acad_group_lov_descr"),
                    "acad_org_lov_descr": course.get("acad_org_lov_descr"),
                    "campus": course.get("campus"),
                    "campus_lov_descr": course.get("campus_lov_descr"),
                    "last_offered": last_term.get("strm_lov_descr") if last_term else None
                }

                return extracted
            except KeyError as e:
                print(f"Missing expected key: {e}")
                return {}


        endpoint = f"/curriculum/courses/crse_id/{course_id}/crse_offer_nbr/{course_offer_number}"
        api_response = self._make_request(endpoint)

        if not api_response:
            return []
            
        return extract_course_info(api_response)
    
    def get_class_section(self, crse_id: str, crse_offer_nbr: str, strm: str = None, session_code: str = "1", class_section: str = "01") -> Optional[Dict]:
        """
        Try to find class section info across all terms for a given course.

        Args:
            crse_id: The course ID
            crse_offer_nbr: The course offering number
            session_code: Defaults to "1"
            class_section: Defaults to "01"

        Returns:
            A dictionary with simplified class section data or None if not found
        """

        def extract_relevant_info(api_response: dict) -> Optional[Dict]:
            try:
                class_section_data = (
                    api_response["ssr_get_class_section_resp"]
                                ["class_section_result"]
                                .get("class_sections", {})
                                .get("ssr_class_section")
                )
                if not class_section_data:
                    return None

                
                return {
                    "crse_id": class_section_data.get("crse_id"),
                    "course_title_long": class_section_data.get("course_title_long"),
                    "class_section": class_section_data.get("class_section"),
                    "session_code": class_section_data.get("session_code"),
                    "term": class_section_data.get("strm_lov_descr"),
                    "location": class_section_data.get("location_descr"),
                    "instructor": class_section_data.get("class_meeting_patterns", {})["class_meeting_pattern"].get("ssr_instr_long"),
                    "instructor_mode": class_section_data.get("instruction_mode_lov_descr"),
                    "start_date": class_section_data.get("start_dt"),
                    "end_date": class_section_data.get("end_dt"),
                    "enrollment_total": class_section_data.get("enrl_tot"),
                    "enrollment_capacity": class_section_data.get("enrl_cap"),
                    "available_seats": class_section_data.get("available_seats"),
                    "schedule": class_section_data.get("ssr_date_long"),
                    "description": class_section_data.get("descrlong")
                }
            except Exception as e:
                print(f"Error parsing class section: {e}")
                return None

        # Try each term in order
        if strm is not None:
            # If strm is provided, use it directly
            endpoint = f"/curriculum/classes/strm/{strm}/crse_id/{crse_id}/crse_offer_nbr/{crse_offer_nbr}/session_code/{session_code}/class_section/{class_section}"
            api_response = self._make_request(endpoint)
            if api_response:
                return extract_relevant_info(api_response)

        else:
            for strm_code in self.terms:
                endpoint = f"/curriculum/classes/strm/{strm_code}/crse_id/{crse_id}/crse_offer_nbr/{crse_offer_nbr}/session_code/{session_code}/class_section/{class_section}"
                api_response = self._make_request(endpoint)
                if not api_response:
                    continue

                # Check if class exists in the response
                result = extract_relevant_info(api_response)
                if result:
                    return result  # Return first valid result

        # If no class found in any term
        return None

        

def main():
    duke_api_service = CurriculumApiService(os.getenv('DUKE_API_BASE_URI'), os.getenv('DUKE_API_KEY'))
    courses = duke_api_service.get_courses_by_subject('AAAS')
    course = duke_api_service.get_course_details('020998', '1')
    course = duke_api_service.get_class_section('027041', '1')
    print(course)

if __name__=='__main__':
    main()