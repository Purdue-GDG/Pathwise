import Image from "next/image";
import styles from "./page.module.css";
import Form from "next/form";
import { submitToBackend } from './api/submit/submitToBackend';

async function createPost(formData) {
  'use server';
  
  const major = formData.get('major');
  const academicInterests = formData.get('academicInterests');
  const courseType = formData.get('courseType');
  
  // Structure the data as JSON
  const formDataJson = {
    major: major || null,
    academicInterests: academicInterests || null,
    courseType: courseType || null,
  };
  
  // This directly calls the backend API
  try {
    const result = await submitToBackend(formDataJson);
    console.log('Submission result:', result);
  } catch (error) {
    console.error('Error sending data to backend:', error);
  }
}

export default function Home() {
  return (
    <div className={styles.formContainer}>
      <div>Select your major</div>
      <form action={createPost} className={styles.formField}>
        <select name="major" className={styles.inputField}>
          <option value="AI">AI</option>
          <option value="CS">CS</option>
          <option value="DS">DS</option>
        </select>
        <button type="submit" className={styles.submitButton}>Submit</button>
      </form>

      <form action={createPost}>
        <div>What primarily describes your academic interests?</div>
        <select name="academicInterests" className={styles.inputField}>
          <option value="Biotech">Biotech</option>
          <option value="Finance">Finance</option>
          <option value="Psychology">Psychology</option>
        </select>
        <button type="submit" className={styles.submitButton}>Submit</button>
      </form>

      <form action={createPost}>
        <div>Type of Courses</div>
        <select name="courseType" className={styles.inputField}>
          <option value="Graduation Plan">Graduation Plan</option>
          <option value="Gen Eds">Gen Eds</option>
          <option value="Electives">Electives</option>
        </select>
        <button type="submit" className={styles.submitButton}>Submit</button>
      </form>
    </div>
  );
}
