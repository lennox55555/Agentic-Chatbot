from langchain.tools import BaseTool
from typing import Dict, List, Optional, Type
from pydantic import BaseModel, Field
from services.duke_api_service.curriculum import CurriculumApiService
from services.duke_api_service.places import PlacesApiService
from services.duke_api_service.events import EventsApiService
import os
import logging

# Define input schemas for our tools
class SubjectCodeInput(BaseModel):
    subject_code: str = Field(description="The subject code (e.g., 'COMPSCI')")

class CourseDetailsInput(BaseModel):
    query: str = Field(description="The course ID and offer number, e.g., 'CS101,01'. In some cases, it could also include the term e.g 'CS101,1,1940 - 2025 Fall Term'")

# Define input schemas for our tools
class PlaceValueInput(BaseModel):
    place_value: str = Field(description="The place value (e.g., 'west_campus', 'east_campus', 'dining')")

class PlaceIdInput(BaseModel):
    place_id: str = Field(description="The ID of the place to get details for")

class EmptyInput(BaseModel):
    """Empty input schema for tools that don't require inputs."""
    pass

class EventInput(BaseModel):
    future_days: str = Field(description="Number of future days to look for events")

# Initialize the API service
curriculum_api_service = CurriculumApiService(
    os.getenv('DUKE_API_BASE_URI'), 
    os.getenv('DUKE_API_KEY')
)

# Initialize the API service
places_api_service = PlacesApiService(
    os.getenv('DUKE_API_BASE_URI'), 
    os.getenv('DUKE_API_KEY')
)

events_api_service = EventsApiService(
    os.getenv('DUKE_API_EVENTS_BASE_URI'),
    os.getenv('DUKE_API_KEY')
)

class GetCoursesBySubjectTool(BaseTool):
    name: str = "get_courses_by_subject"
    description: str = (
        "Get all courses for a specific subject code (e.g., 'COMPSCI', 'MATH').",
        "Always start with this api call to retrieve the different course IDs once the subject has been figured out."
        "Using this tool is important to learn about all courses in a subject, retrieve their IDs, the semester (term) when they are offered, along other helpful information"
    )
    args_schema: Type[BaseModel] = SubjectCodeInput
    
    def _run(self, subject_code: str) -> List[Dict]:
        return curriculum_api_service.get_courses_by_subject(subject_code)
    
    def _arun(self, subject_code: str):
        # Async implementation if needed
        raise NotImplementedError("Async not implemented")

class GetCourseDetailsTool(BaseTool):
    name: str = "get_course_details"
    description: str = (
        "Get detailed information about a specific course using course ID and offer number"
        "If you are looking for the course ID, you can use the get_courses_by_subject tool to retrieve the different classes"
        "If you know the course number like AIPI540, you still need to use the course ID and offer number to get the details, which you can get by using the tool get_courses_by_subject"
        "If there is missing information like the course id (which is different from say AIPI540), either request the user for it or utilize get_courses_by_subject tool to retrieve the different classes, which includes the class ID"
    )
    args_schema: Type[BaseModel] = CourseDetailsInput
    
    def _run(self, query: str) -> Dict:
        parts = [p.replace(" ", "")for p in query.split(',')]
        if len(parts) != 2 or not all(parts):
            # If not valid, try splitting by dash
            parts = [p.strip() for p in query.split('-')]
        
        print('\n parts extracted from query: ', parts)
        if len(parts) != 2 or not all(parts):
            return {
                "error": "Invalid input format. Use 'COURSE_ID-OFFER_NUMBER' or 'COURSE_ID,OFFER_NUMBER'"
            }

        course_id, course_offer_number = parts
        result = curriculum_api_service.get_course_details(course_id, 1)
        return result or {"error": "Invalid input format. Use 'COURSE_ID,OFFER_NUMBER'"}
    
    def _arun(self, query: str):
        # Async implementation if needed
        raise NotImplementedError("Async not implemented")

class GetCourseSectionTool(BaseTool):
    name: str = "get_course_with_extreme_details"
    description: str = (
        "Get extremely detailed information about a specific course using the course ID, offer number, and semester (STRM)"
        "This tool should be used if the user asks for specific details about a course like who the professor is or the description of the course"
        "This tool should utilize get_course_details tool first since it provides some relevant information that will be helpful here"
        "The STRM is a string representing a term range. Here's how it should be mapped: "
        "any classes in the fall term should be mapped to '1940 - 2025 Fall Term'"
        "any classes in the spring term should be mapped to '1910 - 2025 Spring Term'"
        "any classes in the summer term 1 should be mapped to '1925 - 2025 Summer Term 1'"
        "any classes in the summer term 2 should be mapped to '1930 - 2025 Summer Term 2'"
    )
    args_schema: Type[BaseModel] = CourseDetailsInput  # we can reuse this

    def _run(self, query: str) -> Dict:
        try:
            parts = [p.strip() for p in query.split(',')]
            print('\n parts extracted from query in get_course_with_extreme_details: ', parts)
            if len(parts) != 3 or not all(parts):
                # If not valid, try splitting by dash
                parts = [p.strip() for p in query.split('-')]
            course_id, course_offer_number, strm = parts
            print('query received in get course section tool:', query)
            return curriculum_api_service.get_class_section(course_id, course_offer_number, strm)
        except Exception as e:
            return {"error": f"Invalid input format or issue fetching course details from its section: {e}"}

    def _arun(self, query: str):
        raise NotImplementedError("Async not implemented")

# class ListAvailableSubjectsTool(BaseTool):
#     name: str = "list_available_subjects"
#     description: str = "Get a list of all available subject codes and their descriptions"
    
#     def _run(self) -> Dict:
#         # This assumes subjects are available in the API service
#         return {"subjects": curriculum_api_service.subjects}
    
#     def _arun(self):
#         raise NotImplementedError("Async not implemented")

class GetPlacesByValueTool(BaseTool):
    name: str = "get_places_by_value"
    description: str = "Get all places for a specific place value (e.g., 'east_campus', 'west_campus', 'dining', 'central_campus', 'dukecard')"
    args_schema: Type[BaseModel] = EventInput
    
    def _run(self, place_value: str) -> List[Dict]:
        return places_api_service.get_places_by_value(place_value)
    
    def _arun(self, place_value: str):
        # Async implementation if needed
        raise NotImplementedError("Async not implemented")

class GetAllPlacesTool(BaseTool):
    name: str = "get_all_places"
    description: str = "Get all places across all categories (east_campus, west_campus, dining, etc.)"
    args_schema: Type[BaseModel] = EmptyInput

    def _run(self, **kwargs) -> List[Dict]:
        print("running here")
        return places_api_service.get_places_by_all_values()
    
    def _arun(self, **kwargs):
        # Async implementation if needed
        raise NotImplementedError("Async not implemented")

class GetPlaceDetailsByIdTool(BaseTool):
    name: str = "get_place_details_by_id"
    description: str = "Get detailed information about a specific place using its ID"
    args_schema: Type[BaseModel] = PlaceIdInput
    
    def _run(self, place_id: str) -> Dict:
        result = places_api_service.get_place_details_by_id(place_id)
        return result or {"error": f"No details found for place ID: {place_id}"}
    
    def _arun(self, place_id: str):
        # Async implementation if needed
        raise NotImplementedError("Async not implemented")

class GetEventsByFutureDaysTool(BaseTool):
    name: str = "get_events_by_future_days"
    description: str = (
        "Get events happening in the future for a specified number of days"
        "This tool should be used if the user asks for events happening in the future at Duke University"
        "Use the information from the sponsor and co-sponsors to determine which event the user is interested in if they ask for specific events or event categories"
    )
    args_schema: Type[BaseModel] = EventInput

    def _run(self, future_days: str) -> Dict:
        print(f'\n\nfuture_days', future_days)
        result = events_api_service.get_future_events(future_days)
        return result or {"error": f"No details found for events happening in {future_days}"}
    
    def _arun(self, place_id: str):
        # Async implementation if needed
        raise NotImplementedError("Async not implemented")
    

def get_curriculum_tools():
    """Return a list of all curriculum-related tools"""
    return [
        GetCoursesBySubjectTool(),
        GetCourseDetailsTool(),
        GetCourseSectionTool()
        # ListAvailableSubjectsTool()
    ]

def get_location_tools():
    """Return a list of all location-related tools"""
    return [
        GetPlacesByValueTool(),
        # GetAllPlacesTool(),
        GetPlaceDetailsByIdTool()
    ]

def get_events_tools():
    """Return a list of all events-related tools"""
    return [
        GetEventsByFutureDaysTool()
    ]