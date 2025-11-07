import Image from "next/image";
import styles from "./page.module.css";
import Form from "next/form";

async function createPost(formData) {
  'use server';
  const title = formData.get('title');
  console.log(title);
}

export default function Home() {
  return (
    <div className={styles.formContainer}>
      <div>Select your major</div>
      <form action={createPost} className={styles.formField}>
        <select name="title" className={styles.inputField}>
          <option value="AI">AI</option>
          <option value="CS">CS</option>
          <option value="DS">DS</option>
        </select>
        <button type="submit" className={styles.submitButton}>Submit</button>
      </form>

      <form action={createPost}>
        <div>What primarily describes your academic interests?</div>
        <select name="title" className={styles.inputField}>
          <option value="Biotech">Biotech</option>
          <option value="Finance">Finance</option>
          <option value="Psychology">Psychology</option>
        </select>
        <button type="submit" className={styles.submitButton}>Submit</button>
      </form>

      <form action={createPost}>
        <div>Type of Courses</div>
        <select name="title" className={styles.inputField}>
          <option value="Graduation Plan">Graduation Plan</option>
          <option value="Gen Eds">Gen Eds</option>
          <option value="Electives">Electives</option>
        </select>
        <button type="submit" className={styles.submitButton}>Submit</button>
      </form>
    </div>
  );
}
