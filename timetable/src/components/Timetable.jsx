import React from 'react';
import './Timetable.css'
const Timetable = ({ data }) => {
  // Define days and time slots
  const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday'];
  const timeSlots = ['8:30-10:00', '10:10-11:40', '11:45-13:15', '13:20-14:50', '15:00-16:30'];
  

  return (
    
    <div className="timetable-container">
      <h2>Group Timetables</h2>

      {Object.entries(data).map(([groupNumber, groupCourses]) => {
        // Initialize empty timetable grid for this group
        const timetable = Array(days.length).fill().map(() => Array(timeSlots.length).fill(null));

        // Populate the timetable with this group's courses
        Object.entries(groupCourses).forEach(([courseName, sessions]) => {
          sessions.forEach(session => {
            const dayIndex = session.day - 1;
            const slotIndex = session.slot - 1;
            
            if (dayIndex >= 0 && dayIndex < days.length && 
                slotIndex >= 0 && slotIndex < timeSlots.length) {
              timetable[dayIndex][slotIndex] = {
                courseName,
                courseType: session.course_type,
                teacherId: session.teacher_id
              };
            }
          });
        });

        return (
          <div key={groupNumber} className="group-timetable">
            <h3>Group {groupNumber}</h3>
            <table className="timetable">
              <thead>
                <tr>
                  <th>Time/Day</th>
                  {days.map((day, index) => (
                    <th key={index}>{day}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {timeSlots.map((time, slotIndex) => (
                  <tr key={slotIndex}>
                    <td className="time-slot">{time}</td>
                    {days.map((_, dayIndex) => {
                      const cell = timetable[dayIndex][slotIndex];
                      return (
                        <td key={dayIndex} className="timetable-cell">
                          {cell ? (
                            <div className="course-entry">
                              <div className="course-name">{cell.courseName}</div>
                              <div className="course-type">{cell.courseType.split('_')[1]}</div>
                              <div className="teacher">Teacher: {cell.teacherId}</div>
                            </div>
                          ) : null}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        );
      })}
    </div>
  );
};

export default Timetable;