import React from 'react';
import Timetable from './components/Timetable';
import {useState} from 'react';

const timetableData = {
  "1": {
    "Sécurité": [
      {
        "course_type": "Sécurité_lecture",
        "day": 1,
        "slot": 1,
        "teacher_id": 1
      },
      {
        "course_type": "Sécurité_td",
        "day": 1,
        "slot": 2,
        "teacher_id": 1
      }
    ]
  },
  "2": {
    "Recherche opérationnelle 2": [
      {
        "course_type": "Recherche opérationnelle 2_lecture",
        "day": 2,
        "slot": 5,
        "teacher_id": 5
      }
    ]
  }
};

function App() {

  const [schedule, setSchedule] = useState();
  
  const getSchedule = async () => {
    const response = await fetch('http://127.0.0.1:5000/api/schedule');
    const time_table = await response.json();
    setSchedule(time_table);
  }

  return (
    schedule ? (
    <div className="App">
      <button onClick={() => getSchedule()}>
        Get Schedule
      </button>
      <Timetable data={schedule} />
    </div>) : (<button onClick={() => getSchedule()}>
        Get Schedule
      </button>)
  );
}

export default App;